from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SaltrockGBSpider(JSONBlobSpider):
    name = "saltrock_gb"
    item_attributes = {"brand": "Saltrock", "brand_wikidata": "Q7406195"}
    start_urls = ["https://stockist.co/api/v1/u24162/locations/all"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
