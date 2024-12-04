import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class DuffysSpider(scrapy.Spider):
    name = "duffys"
    item_attributes = {"brand": "Duffy's", "extras": {"amenity": "restaurant", "cuisine": "american"}}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.duffysmvp.com/api/app/nearByLocations",
            data={"latitude": "26.6289791", "longitude": "-80.0724384"},
        )

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = store["code"]
            yield item
