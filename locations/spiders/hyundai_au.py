from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiAUSpider(JSONBlobSpider):
    name = "hyundai_au"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/au/services/v1/findadealer?postcode=0"]
    locations_key = ["allDealers", "dealers"]


    def parse(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_feature_array(response, response.json()["allDealers"]["dealers"]) or []
        yield from self.parse_feature_array(response, response.json()["allDealers"]["serviceDealers"]) or []
        yield from self.parse_feature_array(response, response.json()["allDealers"]["partsDealers"]) or []

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("closed"):
            return

        item["ref"] = feature.get("code", feature.get("dealerCode"))
        item["branch"] = feature.get("tradingName")

        if "testDriveModels" in feature.keys():
            apply_category(Categories.SHOP_CAR, item)
            item["ref"] = item["ref"] + "_Sales"
        elif "newWinBkAServiceMobile" in feature.keys():
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            item["ref"] = item["ref"] + "_Service"
        else:
            apply_category(Categories.SHOP_CAR_PARTS, item)
            item["ref"] = item["ref"] + "_Parts"

        yield item
