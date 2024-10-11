import json

import scrapy

from locations.categories import Categories
from locations.geo import MILES_TO_KILOMETERS, vincenty_distance
from locations.items import Feature
from locations.searchable_points import open_searchable_points

DAYS_NAME = {
    "MO": "Mo",
    "TU": "Tu",
    "WE": "We",
    "TH": "Th",
    "FR": "Fr",
    "SA": "Sa",
    "SU": "Su",
}
USPS_URL = "https://tools.usps.com/UspsToolsRestServices/rest/POLocator/findLocations"
USPS_HEADERS = {
    "origin": "https://tools.usps.com",
    "referer": "https://tools.usps.com/find-location.htm?",
    "content-type": "application/json;charset=UTF-8",
}


class UspsCollectionBoxesSpider(scrapy.Spider):
    name = "usps_collection_boxes"
    item_attributes = {
        "brand": "United States Postal Service",
        "brand_wikidata": "Q668687",
        "extras": Categories.POST_BOX.value,
    }
    allowed_domains = ["usps.com"]
    download_delay = 0.1

    def start_requests(self):
        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = tuple(map(float, point.strip().split(",")))

                current_state = json.dumps(
                    {
                        "lbro": "",
                        "requestRefineHours": "",
                        "requestRefineTypes": "",
                        "requestServices": "",
                        "requestType": "collectionbox",
                        "requestGPSLat": "%0.6f" % lat,
                        "requestGPSLng": "%0.6f" % lon,
                        "maxDistance": "100",
                    }
                )

                yield scrapy.Request(
                    USPS_URL,
                    method="POST",
                    body=current_state,
                    headers=USPS_HEADERS,
                    callback=self.parse,
                    meta={
                        "lat": lat,
                        "lon": lon,
                        "radius_miles": 100,
                    },
                )

    def parse_hours(self, hours):
        day_groups = []
        this_day_group = None

        for hour in hours:
            if len(hour["times"]) == 0:
                pass
            else:
                d = hour["dayOfTheWeek"]
                day = DAYS_NAME[d]
                close_time = hour["times"][0]["close"][:-3]

                if not this_day_group:
                    this_day_group = dict(from_day=day, to_day=day, hours=close_time)
                elif this_day_group["hours"] != close_time:
                    day_groups.append(this_day_group)
                    this_day_group = dict(from_day=day, to_day=day, hours=close_time)
                else:
                    this_day_group["to_day"] = day

        day_groups.append(this_day_group)

        collection_times = ""
        for day_group in day_groups:
            if day_group["from_day"] == day_group["to_day"]:
                collection_times += "{from_day} {hours}; ".format(**day_group)
            elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                collection_times += "{hours}; ".format(**day_group)
            else:
                collection_times += "{from_day}-{to_day} {hours}; ".format(**day_group)
        collection_times = collection_times[:-2]

        return collection_times

    def parse(self, response):
        stores = json.loads(response.body)

        stores = stores.get("locations") or []

        if len(stores) == 199 and response.meta.get("radius_miles") > 2:
            # Hit max, so recurse with smaller radius
            steps = 6
            new_radius_miles = int(response.meta.get("radius_miles") / 2.0)

            for step in range(steps):
                angle = (360.0 / steps) * step

                new_lat, new_lon = vincenty_distance(
                    response.meta.get("lat"),
                    response.meta.get("lon"),
                    new_radius_miles * MILES_TO_KILOMETERS,
                    angle,
                )

                current_state = json.dumps(
                    {
                        "lbro": "",
                        "requestRefineHours": "",
                        "requestRefineTypes": "",
                        "requestServices": "",
                        "requestType": "collectionbox",
                        "requestGPSLat": "%0.6f" % new_lat,
                        "requestGPSLng": "%0.6f" % new_lon,
                        "maxDistance": str(new_radius_miles),
                    }
                )

                yield scrapy.Request(
                    url=USPS_URL,
                    method="POST",
                    body=current_state,
                    headers=USPS_HEADERS,
                    callback=self.parse,
                    meta={
                        "lat": new_lat,
                        "lon": new_lon,
                        "radius_miles": new_radius_miles,
                    },
                )

            return

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
                "extras": {},
            }

            message = store.get("specialMessage")
            if message:
                properties["extras"]["note"] = message

            h = self.parse_hours(store["locationServiceHours"][0]["dailyHoursList"])
            if h:
                properties["extras"]["collection_times"] = h
            if properties.get("name") == "USPS COLLECTION BOX - BLUE BOX":
                properties.pop("name")
            elif properties.get("name") == "USPS COLLECTION BOX - PO LOBBY":
                properties["extras"]["indoor"] = "yes"
                properties.pop("name")
            yield Feature(**properties)
