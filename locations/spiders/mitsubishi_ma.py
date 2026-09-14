import json
from copy import deepcopy
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiMASpider(JSONBlobSpider):
    name = "mitsubishi_ma"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.ma/reseau"]

    def extract_json(self, response: Response) -> list[dict]:
        return json.loads(response.xpath('//*[@id="map"]/@data-branches').get())

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["street_address"] = item.pop("addr_full")
        item.pop("phone", None)

        if "vente" in feature["services"]:
            sales_item = deepcopy(item)
            sales_item["ref"] = f"{item['ref']}-sales"
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item

        if "sav" in feature["services"]:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
