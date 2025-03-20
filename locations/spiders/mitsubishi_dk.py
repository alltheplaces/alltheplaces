from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiDKSpider(JSONBlobSpider):
    name = "mitsubishi_dk"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://mitsubishi-motors.dk/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street", None)
        yield item
