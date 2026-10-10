import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiBWNAZASpider(JSONBlobSpider):
    name = "hyundai_bw_na_za"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.co.bw", "www.hyundai.co.na", "www.hyundai.co.za"]
    start_urls = [
        "https://www.hyundai.co.bw/api/dealerships",
        "https://www.hyundai.co.na/api/dealerships",
        "https://www.hyundai.co.za/api/dealerships",
    ]
    locations_key = "items"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = response.urljoin("/dealers/" + feature["slug"])

        if hours := feature.get("operating_hours"):
            # Day labels run on from the preceding closing time, e.g. "Mon to Fri: 07:00-17:30Sat: 08:30-13:00".
            hours = re.sub(r"(?<=\d)(?=[A-Za-z])", "; ", re.sub(r" & (?:some )?public holidays", "", hours))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)

        service = feature.get("is_service_dealer") or feature.get("commercial_service")
        parts = feature.get("commercial_parts")

        if feature.get("sales") or feature.get("commercial_sales"):
            shop = item.deepcopy()
            apply_category(Categories.SHOP_CAR, shop)
            apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, shop, service)
            apply_yes_no(Extras.VEHICLE_CAR_PARTS_SALES, shop, parts)
            yield shop

        if service:
            service_item = item.deepcopy()
            service_item["ref"] = f"{item['ref']}_service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            apply_yes_no(Extras.VEHICLE_CAR_PARTS_SALES, service_item, parts)
            yield service_item

        if parts:
            parts_item = item.deepcopy()
            parts_item["ref"] = f"{item['ref']}_parts"
            apply_category(Categories.SHOP_CAR_PARTS, parts_item)
            yield parts_item
