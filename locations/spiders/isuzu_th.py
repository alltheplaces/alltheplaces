from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_TH, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.isuzu_jp import ISUZU_SHARED_ATTRIBUTES


class IsuzuTHSpider(JSONBlobSpider):
    name = "isuzu_th"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    allowed_domains = ["www.isuzu-tis.com"]
    start_urls = ["https://www.isuzu-tis.com/api/contentstack"]
    locations_key = "entries"

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {
            "bodyPaint": False,
            "changeTire": False,
            "districtIDs": "",
            "overhaul": False,
            "provinceID": "",
            "route": "getDealersWithQuery",
            "searchText": "",
            "service": True,
            "showroom": True,
            "vehicleType": "lcv",
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["mirai"].get("address")
        item["state"] = feature["mirai"].get("region")
        item["name"] = feature["mirai"].get("name_th")
        item["extras"] = {}
        item["extras"]["name:en"] = feature["mirai"].get("name_en")
        item["lat"] = feature.get("sale", {}).get("lat")
        item["lon"] = feature.get("sale", {}).get("lon")
        item["opening_hours"] = OpeningHours()

        if feature.get("sale"):
            sales_item = item.deepcopy()
            sales_item["email"] = feature["sale"].get("email")
            if len(feature["sale"].get("showroom_tel", [])) >= 1:
                sales_item["phone"] = feature["sale"]["showroom_tel"][0].get("tel")
            hours_text = "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                feature["sale"].get("showroom_hour_mon_fri", ""),
                feature["sale"].get("showroom_hour_sat", ""),
                feature["sale"].get("showroom_hour_sun", ""),
            )
            sales_item["opening_hours"].add_ranges_from_string(hours_text, closed=CLOSED_TH)
            if feature["sale"].get("show_room_cv"):
                # Trucks ("commercial vehicles") for sale
                truck_sales_item = sales_item.deepcopy()
                truck_sales_item["ref"] = "{}_CV_SALES".format(feature["dealer_id"])
                apply_category(Categories.SHOP_TRUCK, truck_sales_item)
                yield truck_sales_item
            if feature["sale"].get("show_room_lcv"):
                # Pick ups / utes ("light commercial vehicles") for sale
                pickup_sales_item = sales_item.deepcopy()
                pickup_sales_item["ref"] = "{}_LCV_SALES".format(feature["dealer_id"])
                apply_category(Categories.SHOP_CAR, pickup_sales_item)
                yield pickup_sales_item

        if feature.get("aftersale"):
            service_item = item.deepcopy()
            if len(feature["aftersale"].get("service_center_tel", [])) >= 1:
                service_item["phone"] = feature["aftersale"]["service_center_tel"][0].get("tel")
            hours_text = "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                feature["aftersale"].get("service_center_hour_mon_fri", ""),
                feature["aftersale"].get("service_center_hour_sat", ""),
                feature["aftersale"].get("service_center_hour_sun", ""),
            )
            service_item["opening_hours"].add_ranges_from_string(hours_text, closed=CLOSED_TH)
            if feature["aftersale"].get("service_cv"):
                # Trucks ("commercial vehicles") serviced
                truck_service_item = service_item.deepcopy()
                truck_service_item["ref"] = "{}_CV_SERVICE".format(feature["dealer_id"])
                apply_category(Categories.SHOP_TRUCK_REPAIR, truck_service_item)
                yield truck_service_item
            if feature["aftersale"].get("service_lcv"):
                # Pick ups / utes ("light commercial vehicles") serviced
                pickup_service_item = service_item.deepcopy()
                pickup_service_item["ref"] = "{}_LCV_SERVICE".format(feature["dealer_id"])
                apply_category(Categories.SHOP_CAR_REPAIR, pickup_service_item)
                yield pickup_service_item
