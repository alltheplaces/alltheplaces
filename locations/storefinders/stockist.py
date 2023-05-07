from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class StockistSpider(Spider):
    dataset_attributes = {"source": "api", "api": "stockist.co"}
    key = ""

    def start_requests(self):
        yield JsonRequest(url=f"https://stockist.co/api/v1/{self.key}/locations/all")

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
