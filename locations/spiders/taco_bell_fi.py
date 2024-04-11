from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.taco_bell import TACO_BELL_SHARED_ATTRIBUTES


class TacoBellFISpider(Spider):
    name = "taco_bell_fi"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    start_urls = ["https://www.tacobell.fi/page-data/ravintolat/page-data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]["data"]["allRestaurants"]["nodes"]:
            yield JsonRequest(
                "https://www.tacobell.fi/page-data/ravintolat/{}/page-data.json".format(location["slug"]),
                self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()["result"]["data"]["restaurantCobaSite"]
        item = Feature()
        item["ref"] = location["cobaID"]
        item["branch"] = location["name"].removeprefix("Taco Bell ")
        item["street_address"] = location["address"]
        item["postcode"] = location["postcode"]
        item["city"] = location["city"]
        item["phone"] = location["phone"]
        item["lat"] = location["lat"]
        item["lon"] = location["lon"]
        item["email"] = location["email"]
        item["website"] = response.urljoin(response.json()["path"])

        item["opening_hours"] = OpeningHours()
        for rule in response.json()["result"]["data"]["restaurantCobaOpeningHours"]["nodes"]:
            if rule["type"] != "ORGANIZATION":
                continue
            item["opening_hours"].add_range(DAYS[rule["dayOfWeek"] - 2], rule["startTime"], rule["endTime"])

        yield item
