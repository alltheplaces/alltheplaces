from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TatraBankaSKSpider(Spider):
    name = "tatra_banka_sk"
    item_attributes = {"brand": "Tatra banka", "brand_wikidata": "Q1718069"}

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            url="https://www.tatrabanka.sk/components/tatrabanka/contact_places/geolocation-ajax_utf-8.jsp",
            formdata={
                "page": "0",
                "url": "/sk/o-banke/pobocky-bankomaty/",
                "searchWithGeolocation": "false",
                "meeting": "true",
                "language": "sk",
                "searchInput": "",
                "searchType": "",
                "openNowOnly": "false",
                "saturdayOpen": "false",
                "sundayOpen": "false",
                "wheelchairAccess": "false",
                "secureBox": "false",
                "branchesWithCashRegister": "false",
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.tatrabanka.sk/sk/o-banke/pobocky-bankomaty/",
                "Accept-Language": "sk-SK",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("places", []):
            if not location.get("active", True) or location.get("temporarilyClosed"):
                continue

            category_name = location.get("category", {}).get("nameUrl")

            if category_name == "centrala":
                continue

            item = self.parse_location(location)

            if category_name == "bankomaty":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, location.get("depositWithdrawal") in ("true", True), False)
            elif category_name in ("pobocky", "pobocky-premium-banking", "firemne-centra"):
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected Tatra banka category: {}".format(category_name))
                continue

            apply_yes_no(Extras.WHEELCHAIR, item, location.get("wheelchairAccess") in ("true", True), False)

            if opening_hours := self.parse_opening_hours(location):
                item["opening_hours"] = opening_hours

            yield item

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)

        item["ref"] = str(location.get("id"))
        item["lat"] = location.get("positionN")
        item["lon"] = location.get("positionE")
        item["city"] = location.get("city", {}).get("name")
        item.pop("website", None)

        if branch := item.pop("name", None):
            item["branch"] = branch

        return item

    def parse_opening_hours(self, location: dict[str, Any]) -> OpeningHours | str | None:
        if location.get("nonstop") in ("true", True):
            return "Mo-Su 00:00-24:00"

        opening_hours = OpeningHours()

        try:
            for rule in location.get("openingHours") or []:
                if not rule.get("active"):
                    continue

                for day in DAYS[int(rule["weekdayFrom"]) : int(rule["weekdayTo"]) + 1]:
                    if rule.get("lunchBreak"):
                        opening_hours.add_range(
                            day,
                            self.format_time(rule["openedFromHour"], rule["openedFromMinute"]),
                            self.format_time(rule["lunchBreakOpenedFromHour"], rule["lunchBreakOpenedFromMinute"]),
                        )
                        opening_hours.add_range(
                            day,
                            self.format_time(rule["lunchBreakOpenedToHour"], rule["lunchBreakOpenedToMinute"]),
                            self.format_time(rule["openedToHour"], rule["openedToMinute"]),
                        )
                    else:
                        opening_hours.add_range(
                            day,
                            self.format_time(rule["openedFromHour"], rule["openedFromMinute"]),
                            self.format_time(rule["openedToHour"], rule["openedToMinute"]),
                        )
        except (KeyError, TypeError, ValueError) as e:
            self.logger.warning("Could not parse opening hours for {}: {}".format(location.get("id"), e))
            return None

        return opening_hours or None

    @staticmethod
    def format_time(hour: int, minute: int) -> str:
        return f"{int(hour):02d}:{int(minute):02d}"
