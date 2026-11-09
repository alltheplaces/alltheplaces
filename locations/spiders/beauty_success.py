from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BeautySuccessSpider(JSONBlobSpider):
    name = "beauty_success"
    item_attributes = {"brand": "Beauty Success", "brand_wikidata": "Q60964499"}
    start_urls = ["https://www.beautysuccess.fr/storelocator/stockist/ajax"]
    locations_key = "store"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature.get("address"), feature.get("address2")])
        item["ref"] = feature["store_code"]
        item.pop("addr_full", None)
        yield item
