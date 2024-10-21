from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MavisUSSpider(JSONBlobSpider):
    name = "mavis_us"
    item_attributes = {"brand": "Mavis", "brand_wikidata": "Q65058420"}
    start_urls = ["https://www.mavis.com/locations/all-stores/"]

    def extract_json(self, response: Response) -> list:
        stores = []
        for state_wise_stores_list in chompjs.parse_js_object(
            (chompjs.parse_js_object(response.xpath('//script[contains(text(),"fullAddress")]/text()').get())[-1])
        )[-1]["children"][-1]["stores"].values():
            stores.extend(state_wise_stores_list)
        return stores

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        label = feature.get("storeHeader", {}).get("fields", {}).get("myStoreLabel")
        if label.startswith("Mavis Tire"):
            item["name"] = "Mavis Tires & Brakes"
        elif label.startswith("Mavis Discount"):
            item["name"] = "Mavis Discount Tire"
        yield item
