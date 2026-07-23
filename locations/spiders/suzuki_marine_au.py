import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.suzuki_marine_jp import SUZUKI_MARINE_SHARED_ATTRIBUTES


class SuzukiMarineAUSpider(JSONBlobSpider):
    name = "suzuki_marine_au"
    item_attributes = SUZUKI_MARINE_SHARED_ATTRIBUTES
    allowed_domains = ["www.suzukimarine.com.au"]
    start_urls = ["https://www.suzukimarine.com.au/find-dealers/dealersByState?state=all"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("LatLong"):
            item["lat"], item["lon"] = feature["LatLong"].split(",")

        if feature.get("Link"):
            item["website"] = "https://www.suzukimarine.com.au" + feature["Link"]

        services = feature.get("Services") or []
        if "Boat Package" in services:
            apply_category(Categories.SHOP_BOAT, item)
            apply_yes_no("boat:repair", item, "Service" in services or "Repower" in services)
        elif "Service" in services or "Repower" in services:
            apply_category(Categories.SHOP_BOAT_REPAIR, item)

        if hours := feature.get("ServiceHours"):
            hours = re.sub(r"<[^>]+>", " ", hours)
            hours = re.sub(r"(\d)\.(\d{2})", r"\1:\2", hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)

        yield item
