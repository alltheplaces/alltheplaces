from copy import deepcopy
from datetime import datetime

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

DAYS_VN = {
    "Thứ 2": "Mo",
    "Thứ 3": "Tu",
    "Thứ 4": "We",
    "Thứ 5": "Th",
    "Thứ 6": "Fr",
    "Thứ 7": "Sa",
    "Chủ nhật": "Su",
}


class MitsubishiVNSpider(JSONBlobSpider):
    name = "mitsubishi_vn"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.com.vn/webapi/v1/wp/dealerNetwork"]
    locations_key = "items"

    def pre_process_data(self, feature):
        feature.update(feature.pop("acf"))
        feature.update(feature.pop("dealer_location"))

    def parse_hours(self, working_items):
        oh = OpeningHours()
        for entry in working_items:
            day = DAYS_VN.get(entry.get("working_date", ""))
            if not day:
                continue
            try:
                open_str, close_str = entry["working_hour"].split(" - ")
                for fmt in ["%I:%M:%S %p", "%I:%M %p"]:
                    try:
                        open_t = datetime.strptime(open_str.strip(), fmt).strftime("%H:%M")
                        close_t = datetime.strptime(close_str.strip(), fmt).strftime("%H:%M")
                        oh.add_range(day, open_t, close_t)
                        break
                    except ValueError:
                        continue
            except Exception:
                continue
        return oh

    def post_process_item(self, item, response, location):
        phone = location.get("phone", "")

        phone_sales = []
        if isinstance(location.get("phone_sales", []), list):
            phone_sales = [p["phone_sale"] for p in location["phone_sales"]]

        phone_services = []
        if isinstance(location.get("phone_services", []), list):
            phone_services = [p["phone_service"] for p in location["phone_services"]]

        services = [s["id"] for s in location.get("dealer_service", [])]

        service_hours = {}
        for si in location.get("service_items", []):
            name = si.get("\x1dservice_name", "").strip()
            service_hours[name] = si.get("working_items", [])

        SALES = 219
        SERVICE_AND_PARTS = 220
        USED_CAR_SALES = 364

        if SALES in services or USED_CAR_SALES in services:
            sales_item = deepcopy(item)
            sales_item["ref"] = f"{item['ref']}-sales"
            sales_item["phone"] = "; ".join(filter(None, phone_sales)) or phone
            sales_item["opening_hours"] = self.parse_hours(service_hours.get("Bán hàng", []))
            apply_category(Categories.SHOP_CAR, sales_item)
            apply_yes_no(Extras.CAR_REPAIR, sales_item, SERVICE_AND_PARTS in services)
            apply_yes_no(Extras.CAR_PARTS, sales_item, SERVICE_AND_PARTS in services)
            apply_yes_no(Extras.USED_CAR_SALES, sales_item, USED_CAR_SALES in services)
            yield sales_item

        if SERVICE_AND_PARTS in services:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-service"
            service_item["phone"] = "; ".join(filter(None, phone_services)) or phone
            service_item["opening_hours"] = self.parse_hours(service_hours.get("Dịch vụ", []))
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            apply_yes_no(Extras.CAR_PARTS, service_item, True)
            yield service_item
