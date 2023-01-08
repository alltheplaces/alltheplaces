from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class StorepointSpider(Spider):
    key = ""

    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(url=f"https://api.storepoint.co/v1/{self.key}/locations")

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["lat"] = location["loc_lat"]
            item["lon"] = location["loc_long"]

            yield from self.parse_item(item, location)

    def parse_item(self, item, location: {}, **kwargs):
        yield item
