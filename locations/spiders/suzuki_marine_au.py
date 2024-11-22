from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
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

        if services_string := feature.get("Services"):
            services_list = loads(services_string)
            if "0" in services_list:
                apply_category(Categories.SHOP_BOAT, item)
                if "1" in services_list:
                    apply_category({"boat:repair": "yes"}, item)
                if "2" in services_list:
                    apply_category({"boat:parts": "yes"}, item)
            elif "1" in services_list:
                apply_category(Categories.SHOP_BOAT_REPAIR, item)
                if "2" in services_list:
                    apply_category({"boat:parts": "yes"}, item)
            elif "2" in services_list:
                apply_category(Categories.SHOP_BOAT_PARTS, item)

            if feature.get("ServicesHours"):
                item["opening_hours"] = OpeningHours()

                # Example opening hours string in source data:
                # "ServiceHours": "<p>Mon - Fri: 8:00am - 5:00pm<br>Sat: 8:00am - 12:00pm<br>Sun: Closed</p>",
                item["opening_hours"].add_ranges_from_string(
                    feature["ServiceHours"].replace("<br>", ", ").replace("<p>", "").replace("</p>", "")
                )

            yield item
