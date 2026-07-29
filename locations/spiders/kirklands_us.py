from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KirklandsUSSpider(JSONBlobSpider):
    name = "kirklands_us"
    item_attributes = {"brand": "Kirkland's", "brand_wikidata": "Q6415714"}
    start_urls = ["https://www.kirklands.com/store-locator/stores.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature.get("store")
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        for key, value in feature.get("hours").items():
            if "_" in key:
                start_day, end_day = key.split("_")
            else:
                start_day = end_day = key
            oh.add_days_range(day_range(start_day, end_day), *value.split("-"), time_format="%I%p")
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)

        yield item
