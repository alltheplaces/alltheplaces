from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page links each restaurant to Red Door's Appfront ordering
# app, whose public branch endpoint has cleaner addresses and coordinates.
#
# The API also includes one "Retail & Merchandise" branch, which is not a
# restaurant and is skipped.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class RedDoorGrillUSSpider(Spider):
    name = "red_door_grill_us"
    item_attributes = {"brand": "Red Door Woodfired Grill"}
    allowed_domains = ["api.appfront.ai"]
    start_urls = [
        "https://api.appfront.ai/BeengoWebService/rest/BusinessService/"
        "getAllBranches/businessId=5f84263952aabc0e2f56acc9"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            if not location.get("isDisplayed") or location.get("name") == "Retail & Merchandise":
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["name"]
            item["website"] = "https://reddoorgrill.com/locations/"
            item["phone"] = location.get("phoneNumber")

            if address := location.get("deliveryAddress"):
                item["street_address"] = " ".join(filter(None, [address.get("number"), address.get("street")]))
                item["city"] = "Kansas City" if address.get("city") == "KCMO" else address.get("city")
                item["state"] = address.get("state")
                item["postcode"] = address.get("zipCode")

            coordinates = location.get("geoPoint") or {}
            item["lat"] = coordinates.get("latitude") or location.get("latitude")
            item["lon"] = coordinates.get("longitude") or location.get("longitude")

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item
