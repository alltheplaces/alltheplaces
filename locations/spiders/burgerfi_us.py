from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BurgerfiUSSpider(JSONBlobSpider):
    name = "burgerfi_us"
    item_attributes = {"brand": "BurgerFi", "brand_wikidata": "Q39045496"}
    start_urls = ["https://www.burgerfi.com/wp-json/burgerfi-locations/v1/locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "opening soon" in item["name"].lower():
            return
        item["ref"] = item["website"].replace(" ", "-")
        yield item
