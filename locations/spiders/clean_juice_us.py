from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# The chain's ordering platform, Novadine, returns every store in one response
# with address, coordinates, phone and per day hours.
#
# Two rows are not stores: a "Gift Card" entry and a "Test Lab".


class CleanJuiceUSSpider(Spider):
    name = "clean_juice_us"
    item_attributes = {"brand": "Clean Juice", "brand_wikidata": "Q60775550"}
    allowed_domains = ["order.cleanjuice.com"]
    start_urls = ["https://order.cleanjuice.com/api/stores?all_stores=true"]

    def start_requests(self) -> Iterable[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            name = (location.get("name") or "").strip()
            if name in ("Gift Card", "Test Lab"):
                continue

            item = DictParser.parse(location)
            item["ref"] = location["store_id"]
            item["name"] = None
            # "Agoura Hills, CA"
            item["branch"] = name.rsplit(",", 1)[0].strip()
            item["street_address"] = ", ".join(
                part.strip() for part in [location.get("address1"), location.get("address2")] if part and part.strip()
            )

            item["opening_hours"] = self.parse_opening_hours(location.get("hours") or [])

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "juice"

            yield item

    @staticmethod
    def parse_opening_hours(hours: list[dict]) -> OpeningHours | None:
        """Each entry is {"display_name": "Monday", "start_time": "07:00", "end_time": "18:00"}."""
        oh = OpeningHours()

        for rule in hours:
            if not (day := DAYS_EN.get(rule.get("display_name"))):
                continue
            if (opens := rule.get("start_time")) and (closes := rule.get("end_time")):
                oh.add_range(day, opens, closes)

        return oh if oh else None
