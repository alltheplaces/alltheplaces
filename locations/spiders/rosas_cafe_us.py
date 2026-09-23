import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The store locator is initialised from an ajax/locations.json endpoint which
# returns the whole chain in one response.
#
# The endpoint reuses two of its ids for different restaurants, so the postcode
# is appended to the ref.
#
# Hours are split across up to three free text fields, e.g. "Sun - Thurs:
# 6:30am - 10pm" and "Fri & Sat: 6:30am - 11pm"; one restaurant uses the first
# field for an opening announcement instead.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class RosasCafeUSSpider(Spider):
    name = "rosas_cafe_us"
    item_attributes = {"brand": "Rosa's Cafe"}
    allowed_domains = ["www.rosascafe.com"]
    start_urls = ["https://www.rosascafe.com/ajax/locations.json"]

    def start_requests(self) -> Iterable[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)
            # Two ids are each used by two different restaurants, so the
            # postcode is appended to keep refs unique.
            item["ref"] = f"{location['id']}-{location.get('postal')}"
            item["branch"] = location.get("name")
            item["name"] = None
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(
                part.strip() for part in [location.get("address"), location.get("address2")] if part and part.strip()
            )

            item["opening_hours"] = self.parse_opening_hours(
                [location.get(field) for field in ("hours1", "hours2", "hours3")]
            )

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "tex-mex"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str | None]) -> OpeningHours | None:
        """Parses lines such as "Sun - Thurs: 6:30am - 10pm"."""
        oh = OpeningHours()

        for line in lines:
            line = re.sub(r"\s+", " ", line or "").replace("\u2013", "-").strip()
            if not (
                times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)
            ):
                continue

            days = []
            for token in re.split(r"&|,|\band\b", line[: times.start()].strip(" :")):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        days.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    days.append(day)

            if days:
                oh.add_days_range(
                    days,
                    RosasCafeUSSpider.normalise_time(times.group(1)),
                    RosasCafeUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
