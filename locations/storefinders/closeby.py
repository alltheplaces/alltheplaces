from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class ClosebySpider(Spider):
    dataset_attributes = {"source": "api", "api": "closeby.co"}
    api_key = ""

    def start_requests(self):
        yield JsonRequest(url=f"https://www.closeby.co/embed/{self.api_key}/locations")

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = location.get("address_full")
            yield item
