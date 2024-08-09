from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.searchable_points import open_searchable_points


class BigOTiresUSSpider(Spider):
    name = "big_o_tires_us"
    item_attributes = {"brand": "Big O Tires", "brand_wikidata": "Q4906085"}

    def start_requests(self):
        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = tuple(map(float, point.strip().split(",")))
                params = {"latitude": lat, "longitude": lon, "distanceInMiles": 100}
                yield JsonRequest(
                    "https://www.bigotires.com/restApi/dp/v1/store/storesByLatitudeAndLongitude",
                    data=params,
                    headers={"X-Requested-By": "123"},
                    cb_kwargs={"params": params},
                )

    def parse(self, response, params):
        if "status" not in response.json():
            return get_retry_request(response.request, spider=self, reason="missing status")

        status = response.json()["status"]
        if status["code"] == "002":
            return get_retry_request(response.request, spider=self, reason="status 002")
        elif status["code"] == "013":
            # No stores found
            # Unfortunately, this can also mean "too many stores"
            return
        elif status["code"] != "000":
            self.logger.error(f"Got code {status['code']} for request {params}: {status['description']}")
            return

        if "storesType" not in response.json() or "stores" not in response.json()["storesType"]:
            return get_retry_request(response.request, spider=self, reason="missing stores")

        for location in response.json()["storesType"]["stores"]:
            item = DictParser.parse(location)
            item["phone"] = location["phoneNumbers"][0]
            item["lat"] = location["mapCenter"]["latitude"]
            item["lon"] = location["mapCenter"]["longitude"]
            item["website"] = response.urljoin(location["storeDetailsUrl"])
            item["email"] = location["owner"]["email"]

            oh = OpeningHours()
            for day in location["workingHours"]:
                oh.add_range(day["day"], day["openingHour"], day["closingHour"], "%I:%M %p")
            item["opening_hours"] = oh

            yield item
