from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BeautySuccessSpider(JSONBlobSpider):
    name = "beauty_success"
    item_attributes = {"brand": "Beauty Success", "brand_wikidata": "Q60964499"}
    start_urls = ["https://www.beautysuccess.fr/storelocator/stockist/ajax"]
    locations_key = "store"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = ", ".join(filter(None, [feature.get("address"), feature.get("address2")]))
        item["ref"] = feature["store_code"]
        yield item
