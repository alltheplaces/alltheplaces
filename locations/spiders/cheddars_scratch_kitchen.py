from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours, day_range


class CheddarsScratchKitchenSpider(Spider):
    name = "cheddars_scratch_kitchen"
    item_attributes = {"brand": "Cheddar's", "brand_wikidata": "Q5089187"}
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.cheddars.com/api/restaurants?latitude=40.066479&longitude=-79.889975&resultsPerPage=10000",
            headers={"x-source-channel": "WEB"},
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["restaurants"]:
            location.update(location["contactDetail"].pop("address"))
            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["street_address"] = location["street1"]
            item["branch"] = location["restaurantName"]
            item["phone"] = location["contactDetail"]["phoneDetail"][0]["phoneNumber"]
            item["website"] = "/".join(
                [
                    "https://www.cheddars.com/locations",
                    location["stateCode"].lower(),
                    location["city"].lower().replace(" ", "-"),
                    location["restaurantName"].lower().replace(" - ", "-").replace(" ", "-"),
                    str(item["ref"]),
                ]
            )
            oh = OpeningHours()
            for day_time in location["restaurantHours"][0]["hoursInfo"]:
                if day_time["name"] == "Hours of Operations":
                    start_day = DAYS_FULL[day_time["dayOfWeek"] - 1]
                    end_day = DAYS_FULL[day_time["endDayOfWeek"] - 1]
                    open_time = day_time["startTime"]
                    close_time = day_time["endTime"]
                    oh.add_days_range(day_range(start_day, end_day), open_time, close_time, time_format="%I:%M %p")
            item["opening_hours"] = oh
            yield item

    # async def start(self) -> AsyncIterator[FormRequest]:
    #     url = "https://www.cheddars.com/web-api/restaurants"
    #
    #     with open_searchable_points("us_centroids_100mile_radius.csv") as points:
    #         next(points)  # Ignore the header
    #         for point in points:
    #             _, lat, lon = point.strip().split(",")
    #             formdata = {
    #                 "geoCode": lat + "," + lon,
    #                 "resultsPerPage": "500",
    #                 "resultsOffset": "0",
    #                 "displayDistance": "false",
    #                 "locale": "en_US",
    #             }
    #
    #             yield FormRequest(
    #                 url,
    #                 self.parse,
    #                 method="POST",
    #                 formdata=formdata,
    #             )
    #
    # def parse(self, response):
    #     data = response.json()
    #
    #     try:
    #         for place in data["successResponse"]["locationSearchResult"]["Location"]:
    #             properties = {
    #                 "ref": place["restaurantNumber"],
    #                 "name": place["restaurantName"],
    #                 "street_address": merge_address_lines([place["AddressOne"], place["AddressTwo"]]),
    #                 "city": place["city"],
    #                 "state": place["state"],
    #                 "postcode": place["zip"],
    #                 "country": place["country"],
    #                 "lat": place["latitude"],
    #                 "lon": place["longitude"],
    #                 "phone": place["phoneNumber"],
    #                 "website": response.url,
    #             }
    #
    #             yield Feature(**properties)
    #     except:
    #         pass
