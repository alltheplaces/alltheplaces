from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hamleys import HAMLEYS_SHARED_ATTRIBUTES


class HamleysZASpider(JSONBlobSpider):
    name = "hamleys_za"
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES
    start_urls = ["https://stockist.co/api/v1/map_93g828pq/locations/all"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        oh = OpeningHours()
        for field in feature.get("custom_fields", []):
            if field.get("name") == "Hours":
                oh = self.parse_hours(field.get("value") or "")

        item["opening_hours"] = oh
        apply_category(Categories.SHOP_TOYS, item)

        yield item

    def parse_hours(self, hours_string: str) -> OpeningHours:
        oh = OpeningHours()
        oh.add_ranges_from_string(
            hours_string.replace("h", ":").replace("and Public Holidays", "").replace("Public Holidays", "")
        )
        return oh
