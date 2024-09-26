from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiZASpider(JSONBlobSpider):
    name = "hyundai_za"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["api.hyundai.co.za"]
    start_urls = ["https://api.hyundai.co.za/api/Dealers"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature.get("Description")
        if slug := feature.get("Slug"):
            item["website"] = "https://www.hyundai.co.za/dealers/" + slug
        if feature.get("Sales") or feature.get("CommercialSales"):
            sales = item.copy()
            sales["ref"] = str(feature["Id"]) + "_Sales"
            apply_category(Categories.SHOP_CAR, sales)
            yield sales
        if feature.get("Service") or feature.get("CommercialService"):
            service = item.copy()
            service["ref"] = str(feature["Id"]) + "_Service"
            apply_category(Categories.SHOP_CAR_REPAIR, service)
            yield service
        if feature.get("Parts") or feature.get("CommercialParts"):
            parts = item.copy()
            parts["ref"] = str(feature["Id"]) + "_Parts"
            apply_category(Categories.SHOP_CAR_PARTS, parts)
            yield parts
