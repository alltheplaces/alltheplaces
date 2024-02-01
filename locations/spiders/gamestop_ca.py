from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.gamestop_us import GAMESTOP_SHARED_ATTRIBUTES


class GamestopCASpider(Spider):
    name = "gamestop_ca"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    allowed_domains = ["www.gamestop.ca"]
    start_urls = ["https://www.gamestop.ca/StoreLocator/GetStoresForStoreLocatorByProduct"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            for key, value in location.items():
                if value == "undefined":
                    location[key] = None
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item["phone"] = location["Phones"]
            yield from self.extract_hours(item, location)

    @staticmethod
    def extract_hours(item: Feature, location: dict):
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["Hours"])
        yield item
