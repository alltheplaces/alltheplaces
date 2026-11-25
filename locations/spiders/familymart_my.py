from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FamilymartMYSpider(JSONBlobSpider):
    name = "familymart_my"
    item_attributes = {"brand": "FamilyMart", "brand_wikidata": "Q11247682"}
    start_urls = ["https://d1b9rei9wqfp7s.cloudfront.net/stores.json"]
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
