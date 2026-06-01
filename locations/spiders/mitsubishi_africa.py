from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class MitsubishiAfricaSpider(UberallSpider):
    name = "mitsubishi_africa"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    key = "mmoFptTX9q828jrXV2qSSLTW6c8AAp"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["name"] = item["name"].replace(" by CFAO", "")
        apply_category(Categories.SHOP_CAR, item)
        yield item
