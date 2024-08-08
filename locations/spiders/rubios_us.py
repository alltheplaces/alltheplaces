from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class RubiosUSSpider(Spider):
    name = "rubios_us"
    item_attributes = {"brand": "Rubio's", "brand_wikidata": "Q7376154"}
    custom_settings = {"ROBOTSTXT_OBEY": False}  # No robots.txt. Unparsable HTML error page returned.

    def start_requests(self):
        yield JsonRequest(url="https://apis.rubios.com/olo_api/restaurants")

    def parse(self, response):
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location)
            yield item
