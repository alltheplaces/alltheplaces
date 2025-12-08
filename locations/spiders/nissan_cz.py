from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NissanCZSpider(JSONBlobSpider):
    name = "nissan_cz"
    item_attributes = {"brand": "Nissan", "brand_wikidata": "Q20165"}
    start_urls = [
        "https://ni-content.hu/nissan-dealers/Data/data_cz.json",
    ]
    locations_key = "dealers"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature.get("code"))
        item["lat"] = feature.get("lattitude")
        item["street_address"] = item.pop("addr_full", None)
        if item.get("phone"):
            item["phone"] = item["phone"].replace("Telefon:", "").replace("Mobil:", "").replace("\n", ";")
        service_phone = feature.get("phone2")
        item["extras"]["fax"] = feature.get("fax")

        if feature.get("Service #PV#"):
            car_sales = item.deepcopy()
            car_sales["ref"] += "_car_sales"
            apply_category(Categories.SHOP_CAR, car_sales)
            yield car_sales
        if feature.get("Service #SC#"):
            car_service = item.deepcopy()
            car_service["ref"] += "_car_service"
            if service_phone:
                car_service["phone"] = service_phone
            apply_category(Categories.SHOP_CAR_REPAIR, car_service)
            yield car_service
        if feature.get("Service #TR#"):
            truck_sales = item.deepcopy()
            truck_sales["ref"] += "_truck_sales"
            apply_category(Categories.SHOP_TRUCK, truck_sales)
            yield truck_sales
        if feature.get("Service #TAS#"):
            truck_service = item.deepcopy()
            truck_service["ref"] += "_truck_service"
            if service_phone:
                truck_service["phone"] = service_phone
            apply_category(Categories.SHOP_TRUCK_REPAIR, truck_service)
            yield truck_service
