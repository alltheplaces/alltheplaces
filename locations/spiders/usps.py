import json

import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature

DAYS_NAME = {
    "MO": "Mo",
    "TU": "Tu",
    "WE": "We",
    "TH": "Th",
    "FR": "Fr",
    "SA": "Sa",
    "SU": "Su",
}


class UspsSpider(scrapy.Spider):
    name = "usps"
    item_attributes = {
        "brand": "United States Postal Service",
        "brand_wikidata": "Q668687",
        "extras": Categories.POST_OFFICE.value,
    }
    allowed_domains = ["usps.com"]

    def start_requests(self):
        url = "https://tools.usps.com/UspsToolsRestServices/rest/POLocator/findLocations"

        headers = {
            "origin": "https://tools.usps.com",
            "Referer": "https://tools.usps.com/find-location.htm?",
            "content-type": "application/json;charset=UTF-8",
        }

        with open("./locations/searchable_points/us_centroids_25mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")

                current_state = json.dumps(
                    {
                        "requestGPSLat": lat,
                        "requestGPSLng": lon,
                        "maxDistance": "100",
                        "requestType": "po",
                    }
                )

                yield scrapy.Request(
                    url,
                    method="POST",
                    body=current_state,
                    headers=headers,
                    callback=self.parse,
                )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if len(hour["times"]) == 0:
                pass
            else:
                day = hour["dayOfTheWeek"][:2].title()
                open_time = hour["times"][0]["open"][:-3]
                close_time = hour["times"][0]["close"][:-3]

                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()["locations"]

        for store in stores:
            properties = {
                "ref": store["locationID"],
                "name": store["locationName"],
                "addr_full": store["address1"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip5"],
                "country": "US",
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
            }

            h = self.parse_hours(store["locationServiceHours"][0]["dailyHoursList"])
            if h:
                properties["opening_hours"] = h

            yield Feature(**properties)
