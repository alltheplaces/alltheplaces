from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KringwinkelBESpider(JSONBlobSpider):
    name = "kringwinkel_be"
    item_attributes = {"name": "Kringwinkel", "brand": "De Kringwinkel", "brand_wikidata": "Q55935433"}
    start_urls = ["https://www.kringwinkel.be/json/stores?types=2"]
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Kringwinkel ")
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
