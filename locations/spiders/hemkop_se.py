from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_SE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HemkopSESpider(JSONBlobSpider):
    name = "hemkop_se"
    item_attributes = {"brand": "Hemköp", "brand_wikidata": "Q10521746"}
    start_urls = ["https://www.hemkop.se/axfood/rest/store"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not item["street_address"]:  # Not enough location data
            return

        if not feature.get("open"):
            return

        item["branch"] = (item.pop("name", "") or "").removeprefix("Hemköp ")
        item["phone"] = feature["address"].get("phone")
        item["website"] = "https://www.hemkop.se/butik/{}".format(item["ref"])

        item["opening_hours"] = self.parse_opening_hours(feature.get("openingHours", []))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            day, times = rule.split(" ")
            if day := sanitise_day(day, DAYS_SE):
                oh.add_range(day, *times.split("-"))
        return oh
