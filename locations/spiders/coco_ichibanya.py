from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CoCoIchibanyaSpider(JSONBlobSpider):
    name = "coco_ichibanya"
    item_attributes = {"brand": "CoCo Ichibanya", "brand_wikidata": "Q5986105"}
    start_urls = ["https://worldwide.ichibanya.co.jp/api/point/w/"]
    locations_key = "items"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.RESTAURANT, item)
        yield item
