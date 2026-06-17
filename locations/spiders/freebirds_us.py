from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreebirdsUSSpider(JSONBlobSpider):
    name = "freebirds_us"
    item_attributes = {"brand": "Freebirds", "brand_wikidata": "Q5500367"}
    """
    Brands powered by Thanx can be found on https://www.thanx.com/
    The merchant_id can be found on brand ordering pages following the pattern: https://order.thanx.com/{brand_slug}
    Example: https://order.thanx.com/freebirds
    """
    start_urls = ["https://api.thanx.com/locations?merchant_id=1134"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("coming_soon") is True:
            return
        item["branch"] = item.pop("name").removeprefix("Freebirds - ").removeprefix("Freebirds ").split(",")[0]
        item["street_address"] = item.pop("street")
        item["opening_hours"] = self.parse_opening_hours(feature.get("business_hours", []))
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            opening_hours.add_range(rule["day"], rule["start"], rule["end"])
        return opening_hours
