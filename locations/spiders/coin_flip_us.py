from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CoinFlipUSSpider(JSONBlobSpider):
    name = "coin_flip_us"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    start_urls = ["https://storerocket.io/api/user/56wpZAy8An/locations"]
    locations_key = ["results", "locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = "https://coinflip.tech/bitcoin-atm?location=" + feature["slug"]
        apply_category(Categories.ATM, item)
        apply_yes_no("currency:XBT", item, True)
        yield item
