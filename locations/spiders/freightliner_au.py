from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreightlinerAUSpider(JSONBlobSpider):
    name = "freightliner_au"
    item_attributes = {"brand": "Freightliner", "brand_wikidata": "Q1420724"}
    start_urls = ["https://www.freightliner.com.au/api/dealerlocator/dealerships"]

    SERVICE_CATEGORIES = {
        "Repair & Maintenance": Categories.SHOP_TRUCK_REPAIR,
        "New Vehicle Sales": Categories.SHOP_TRUCK,
        "Parts-Sales": Categories.SHOP_TRUCK_PARTS,
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        communications = feature["communications"]
        item["phone"] = communications.get("phone")
        item["email"] = communications.get("email")
        if website := communications.get("internet"):
            item["website"] = website if website.startswith(("http://", "https://")) else f"https://{website}"

        for service in feature["services"]:
            service_item = item.deepcopy()
            service_item["ref"] = f'{item["ref"]}-{service["serviceId"]}'
            apply_category(self.SERVICE_CATEGORIES[service["name"]], service_item)

            hours = OpeningHours()
            for day in service["openingHours"]:
                if day["closed"]:
                    hours.set_closed(day["day"])
                else:
                    hours.add_range(day["day"], day["from"], day["until"])

            service_item["opening_hours"] = hours
            yield service_item
