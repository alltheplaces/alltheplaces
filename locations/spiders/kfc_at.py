from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KFCATSpider(Spider):
    name = "kfc_at"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["www.kfc.co.at"]
    start_urls = ["https://www.kfc.co.at/api/collections/shops/entries"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["website"] = location.get("permalink")
            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("opening_hours", []):
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day_hours["day_dayname"]["label"], day_hours["start"], day_hours["stop"]
                )
            yield item
