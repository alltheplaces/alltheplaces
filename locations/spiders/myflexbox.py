from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class MyflexboxSpider(Spider):
    name = "myflexbox"
    item_attributes = {"brand_wikidata": "Q117313525"}
    start_urls = ["https://api.myflexbox.de/api/1/lockers", "https://api.myflexbox.at/api/1/lockers"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["lockers"]:
            item = Feature()
            item["ref"] = "{}-{}".format(location["countryCode"], location["externalId"])
            item["housenumber"] = location["streetNumber"]
            item["street"] = location["streetName"]
            item["city"] = location["city"]
            item["country"] = location["countryCode"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]

            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]:
                if day["day"] == "HOLIDAY":
                    continue
                item["opening_hours"].add_range(day["day"], day["startTime"], day["endTime"])

            yield item
