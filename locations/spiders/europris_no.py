from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EuroprisNOSpider(JSONBlobSpider):
    name = "europris_no"
    item_attributes = {"brand": "Europris", "brand_wikidata": "Q17770215"}
    start_urls = ["https://www.europris.no/butikker/stores/get"]
    locations_key = ["stores"]

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = store.get("source_code")
        item["branch"] = item.pop("name").removeprefix("Europris").strip()
        item["street_address"] = item.pop("street", None)
        apply_category(Categories.SHOP_GENERAL, item)
        yield item
