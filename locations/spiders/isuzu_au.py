from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.isuzu_jp import ISUZU_SHARED_ATTRIBUTES


class IsuzuAUSpider(JSONBlobSpider):
    name = "isuzu_au"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    start_urls = ["https://www.isuzuute.com.au/isuzuapi/Dealer/GetAllDealers"]
    locations_key = "Dealers"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        department = feature.get("Sales") or feature.get("Service") or feature["Parts"]
        item["ref"] = feature["Code"]
        item["street_address"] = department["Address"]["Street"]
        item["city"] = department["Address"]["Suburb"]
        item["state"] = department["Address"]["State"]
        item["postcode"] = department["Address"]["PostCode"]
        item["lat"] = department["Map"]["Latitude"]
        item["lon"] = department["Map"]["Longitude"]
        item["phone"] = department["Contact"]["Phone"]
        item["email"] = department["Contact"]["Email1"]
        if website := department["Contact"]["Website"]:
            item["website"] = website["Url"]

        if feature.get("Sales"):
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, item, bool(feature.get("Service")))
        else:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_CAR_PARTS_SALES, item, bool(feature.get("Parts")))

        oh = OpeningHours()
        for day, hours in department["OpeningHours"].items():
            oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh
        yield item
