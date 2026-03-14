from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ZebSpider(JSONBlobSpider):
    name = "zeb"
    item_attributes = {"brand": "ZEB", "brand_wikidata": "Q121879599"}
    start_urls = ["https://www.zeb.be/apps/fashion-society/locations"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ZEB ")
        item["phone"] = feature["address"]["phone"]
        item["lat"] = feature["address"]["latitude"]
        item["lon"] = feature["address"]["longitude"]
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
