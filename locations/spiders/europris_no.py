from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NO, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class EuroprisNOSpider(Spider):
    name = "europris_no"
    item_attributes = {"brand": "Europris", "brand_wikidata": "Q17770215"}
    start_urls = ["https://www.europris.no/butikker/stores/get"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        stores = response.json().get("stores") or []
        for store in stores:
            item = DictParser.parse(store)

            item["ref"] = store.get("source_code")
            item["branch"] = item.pop("name").removeprefix("Europris ")
            item["street_address"] = item.pop("street")
            item["country"] = store.get("country_code")
            item.pop("state")  # Invalid field

            if attributes := store.get("extension_attributes"):
                try:
                    oh = OpeningHours()
                    self.parse_hours(oh, attributes.get("open_hours_workdays"), DAYS_WEEKDAY)
                    self.parse_hours(oh, attributes.get("open_hours_saturday"), ["Sa"])
                    self.parse_hours(oh, attributes.get("open_hours_sunday"), ["Su"])
                    item["opening_hours"] = oh
                except:
                    self.logger.error("Error parsing opening hours")

            apply_category(Categories.SHOP_GENERAL, item)
            yield item

    def parse_hours(self, oh: OpeningHours, hours: str | None, days: list[str]) -> None:
        if not hours:
            return
        if hours.lower() in CLOSED_NO:
            oh.set_closed(days)
        elif "-" in hours:
            open_time, close_time = hours.split("-", 1)
            if open_time.strip().isdigit() and close_time.strip().isdigit():
                oh.add_days_range(days, open_time.strip(), close_time.strip(), "%H")
