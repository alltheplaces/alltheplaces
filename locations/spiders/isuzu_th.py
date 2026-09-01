from typing import Iterable

import chompjs
from scrapy.http import Response, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc
from locations.spiders.isuzu_jp import ISUZU_SHARED_ATTRIBUTES


class IsuzuTHSpider(JSONBlobSpider):
    name = "isuzu_th"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    allowed_domains = ["www.isuzu-tis.com"]
    start_urls = ["https://www.isuzu-tis.com/dealer"]
    SALE_CATEGORIES = {"car": Categories.SHOP_CAR, "truck": Categories.SHOP_TRUCK}
    SERVICE_CATEGORIES = {"car": Categories.SHOP_CAR_REPAIR, "truck": Categories.SHOP_TRUCK_REPAIR}
    CATEGORY_MAPPING = {
        "sale": SALE_CATEGORIES,
        "aftersale": SERVICE_CATEGORIES,
        "bp": SERVICE_CATEGORIES,  # Body/Paint Service
    }

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        scripts = response.xpath("//script[contains(text(), 'open_time')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))
        return DictParser.get_nested_key(data, "data")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        for location_type in ["sale", "aftersale", "bp"]:
            if isinstance(feature.get(location_type), dict):
                location_info = feature[location_type]
                base_item = item.deepcopy()
                base_item["name"] = location_info.get("name_th")
                base_item["addr_full"] = location_info.get("address")
                base_item["email"] = location_info.get("email")
                base_item["ref"] = location_info.get("branch_code")
                if phone := location_info.get("contact", {}).get("main_contact"):
                    base_item["phone"] = phone[0].get("tel")

                if location_info.get("active_cv"):
                    # Trucks ("commercial vehicles")
                    truck_item = base_item.deepcopy()
                    truck_item["ref"] = f'{base_item["ref"]}_cv_{location_type}'
                    apply_category(self.CATEGORY_MAPPING[location_type]["truck"], truck_item)
                    apply_yes_no(Extras.VEHICLE_BODY_REPAIR_SERVICES, truck_item, location_type == "bp")
                    apply_yes_no(Extras.VEHICLE_PAINTING_SERVICES, truck_item, location_type == "bp")
                    yield truck_item

                if location_info.get("active_lcv"):
                    # Pick ups / utes ("light commercial vehicles")
                    pickup_item = base_item.deepcopy()
                    pickup_item["ref"] = f'{base_item["ref"]}_lcv_{location_type}'
                    apply_category(self.CATEGORY_MAPPING[location_type]["car"], pickup_item)
                    apply_yes_no(Extras.VEHICLE_BODY_REPAIR_SERVICES, pickup_item, location_type == "bp")
                    apply_yes_no(Extras.VEHICLE_PAINTING_SERVICES, pickup_item, location_type == "bp")
                    yield pickup_item
