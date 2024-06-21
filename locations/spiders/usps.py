import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature


class UspsSpider(scrapy.Spider):
    name = "usps"
    item_attributes = {
        "brand": "United States Postal Service",
        "brand_wikidata": "Q668687",
        "extras": Categories.POST_OFFICE.value,
    }

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_25mile_radius.csv"):
            yield JsonRequest(
                url="https://tools.usps.com/UspsToolsRestServices/rest/POLocator/findLocations",
                data={"requestGPSLat": lat, "requestGPSLng": lon, "maxDistance": "100", "requestType": "PO"},
            )

    @staticmethod
    def parse_hours(rules) -> OpeningHours:
        opening_hours = OpeningHours()

        for rule in rules:
            for time in rule["times"]:
                opening_hours.add_range(
                    day=rule["dayOfTheWeek"], open_time=time["open"], close_time=time["close"], time_format="%H:%M:%S"
                )

        return opening_hours

    def parse(self, response, **kwargs):
        for store in response.json().get("locations", []):
            properties = {
                "ref": store["locationID"],
                "name": store["locationName"],
                "street_address": store["address1"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip5"] + "-" + store["zip4"],
                "country": "US",
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
            }
            for service in store["locationServiceHours"]:
                if service["name"] == "BUSINESS":
                    properties["opening_hours"] = self.parse_hours(service["dailyHoursList"])
                    break

            yield Feature(**properties)
