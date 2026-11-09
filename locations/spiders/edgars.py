import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EdgarsSpider(JSONBlobSpider):
    name = "edgars"
    start_urls = ["https://www.edgars.co.za/pages/store-locator"]
    item_attributes = {"brand": "Edgars", "brand_wikidata": "Q97276073"}

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath('//script[@id="storeLocatorMetaobjects"]/text()').get())

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["name"]
        item["branch"] = item.pop("name").removeprefix("Edgars ")
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
