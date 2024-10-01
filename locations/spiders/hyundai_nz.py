from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiNZSpider(JSONBlobSpider):
    name = "hyundai_nz"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.co.nz"]
    start_urls = ["https://www.hyundai.co.nz/hyundai/locations"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for region in response.json()["Regions"]:
            yield from self.parse_feature_array(response, region["Dealers"])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["Value"])
        item["branch"] = item.pop("name", None)
        item.pop("email", None)  # E-mail of primary contact person only. Ignore.

        if isinstance(feature.get("Type"), list) and len(feature["Type"]) > 0:
            if feature["Type"][0] == "Passenger sales and service":
                service_feature = item.deepcopy()
                apply_category(Categories.SHOP_CAR, item)
                item["ref"] = item["ref"] + "_Sales"
                apply_category(Categories.SHOP_CAR_REPAIR, service_feature)
                service_feature["ref"] = service_feature["ref"] + "_Service"
                yield item
                yield service_feature
            elif feature["Type"][0] == "Service only agents":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
                item["ref"] = item["ref"] + "_Service"
                yield item
            elif feature["Type"][0] == "Truck sales and service":
                service_feature = item.deepcopy()
                apply_category(Categories.SHOP_TRUCK, item)
                item["ref"] = item["ref"] + "_Sales"
                apply_category(Categories.SHOP_TRUCK_REPAIR, service_feature)
                service_feature["ref"] = service_feature["ref"] + "_Service"
                yield item
                yield service_feature
            elif feature["Type"][0] == "Marine":
                apply_category(Categories.SHOP_BOAT, item)
                apply_category({"boat:repair": "yes"}, item)
                apply_category({"boat:parts": "yes"}, item)
                yield item
            else:
                raise ValueError("Unknown feature type: {}".format(feature["Type"][0]))
