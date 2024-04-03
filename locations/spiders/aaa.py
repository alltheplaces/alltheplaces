from urllib.parse import urlencode

import scrapy

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.items import Feature


class AAASpider(scrapy.Spider):
    name = "aaa"
    item_attributes = {
        "brand": "American Automobile Association",
        "brand_wikidata": "Q463436",
    }
    allowed_domains = ["tdr.aaa.com"]

    def start_requests(self):
        point_files = [
            "us_centroids_50mile_radius.csv",
            "ca_centroids_50mile_radius.csv",
        ]
        for lat, lon in point_locations(point_files):
            params = {
                "searchtype": "O",
                "radius": "5000",
                "format": "json",
                "ident": "AAACOM",
                "destination": f"{lat},{lon}",
            }
            yield scrapy.http.Request("https://tdr.aaa.com/tdrl/search.jsp?" + urlencode(params))

    def parse(self, response):
        locations = response.json()["aaa"]["services"].get("travelItems")
        if not locations:
            return
        locations = locations.get("travelItem", [])
        # If result is a singleton POI then it is not supplied as a list! Make consistent.
        if not isinstance(locations, list):
            locations = [locations]
        for location in locations:
            properties = {
                "ref": location["id"],
                "name": location["itemName"],
                "street_address": location["addresses"]["address"]["addressLine"],
                "city": location["addresses"]["address"]["cityName"],
                "state": location["addresses"]["address"]["stateProv"]["code"],
                "postcode": location["addresses"]["address"]["postalCode"],
                "country": location["addresses"]["address"]["countryName"]["code"],
                "lat": location["position"]["latitude"],
                "lon": location["position"]["longitude"],
                "phone": location["phones"].get("phone", {}).get("content"),
            }
            item = Feature(**properties)
            apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
            yield item
