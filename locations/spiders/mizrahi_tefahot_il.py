import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MizrahiTefahotILSpider(Spider):
    name = "mizrahi_tefahot_il"
    item_attributes = {"brand": "מזרחי טפחות", "brand_wikidata": "Q2777129"}

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            url="https://www.mizrahi-tefahot.co.il/umbraco/api/searchBranches/GetCurrentLocationBranches",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body="siteLang=he-IL",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("result", []):
            if not self.has_coordinates(location):
                continue

            item = DictParser.parse(location)
            item["ref"] = location.get("misparSnif")
            item["branch"] = self.clean_text(location.get("shemSnif"))
            item["street_address"] = self.clean_text(location.get("ktovet"))
            item["city"] = self.clean_text(location.get("shemYeshuv"))
            item["email"] = location.get("emailSnif")
            item["lat"] = location.get("y_Coordinate")
            item["lon"] = location.get("x_Coordinate")
            item.pop("name", None)

            if postcode := location.get("mikud"):
                if postcode != "00000":
                    item["postcode"] = postcode
                else:
                    item.pop("postcode", None)

            if opening_hours := self.parse_opening_hours(location):
                item["opening_hours"] = opening_hours

            # The locator renders shekel ATMs when kaspon == "0"; FX ATMs use 1/2/9 currency codes.
            has_atm = location.get("kaspon") == "0" or location.get("kasponMatach") in {"1", "2", "9"}
            apply_yes_no(Extras.ATM, item, has_atm)
            apply_yes_no(Extras.WHEELCHAIR, item, location.get("gishaN") == "1")
            apply_category(Categories.BANK, item)
            yield item

    def parse_opening_hours(self, location: dict[str, Any]) -> OpeningHours | None:
        opening_hours = OpeningHours()
        for rule in location.get("openingHours", []):
            try:
                days = self.parse_days(rule.get("yemeiPtichaEnglish"))
                ranges = self.parse_time_ranges(rule.get("sheotPticha"))
                for day in days:
                    for open_time, close_time in ranges:
                        opening_hours.add_range(day, open_time, close_time)
            except ValueError:
                continue
        return opening_hours if opening_hours else None

    def parse_days(self, value: str | None) -> list[str]:
        if not value:
            return []
        value = value.split("&", 1)[0].upper()
        day_map = {"SUN": "Su", "MON": "Mo", "MUN": "Mo", "TUE": "Tu", "WED": "We", "THU": "Th", "FRI": "Fr"}
        days = [day_map[day] for day in re.findall(r"SUN|MON|MUN|TUE|WED|THU|FRI", value)]
        if "-" in value and len(days) >= 2:
            israel_week = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
            start = israel_week.index(days[0])
            end = israel_week.index(days[-1])
            return israel_week[start : end + 1] if start <= end else israel_week[start:] + israel_week[: end + 1]
        return list(dict.fromkeys(days))

    def parse_time_ranges(self, value: str | None) -> list[tuple[str, str]]:
        value = re.sub(r"[\u200e\u200f]", "", value or "")
        times = [self.parse_time(time) for time in re.findall(r"\d{2}\s*:\s*\d{2}", value)]
        ranges = []
        for index in range(0, len(times) - 1, 2):
            first = times[index]
            second = times[index + 1]
            if first > second:
                first, second = second, first
            if first != second:
                ranges.append((first, second))
        return sorted(set(ranges))

    def parse_time(self, value: str) -> str:
        # Source RTL time strings are stored as MM:HH, e.g. 30:08 means 08:30.
        minute, hour = [int(part) for part in value.split(":")]
        if hour > 23 or minute > 59:
            raise ValueError
        return "{:02d}:{:02d}".format(hour, minute)

    def has_coordinates(self, location: dict[str, Any]) -> bool:
        try:
            return bool(float(location.get("x_Coordinate")) and float(location.get("y_Coordinate")))
        except (TypeError, ValueError):
            return False

    def clean_text(self, value: str | None) -> str | None:
        if not value:
            return None
        return re.sub(r"\s+", " ", value.replace("\u200f", "")).strip()
