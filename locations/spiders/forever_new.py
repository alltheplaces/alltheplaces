import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ForeverNewSpider(Spider):
    name = "forever_new"
    item_attributes = {"brand": "Forever New", "brand_wikidata": "Q119221929"}
    allowed_domains = ["www.forevernew.com.au", "www.forevernew.co.nz"]
    start_urls = [
        "https://www.forevernew.com.au/locator/index/search/?longitude=0&latitude=0&radius=100000&type=all",
        "https://www.forevernew.co.nz/locator/index/search/?longitude=0&latitude=0&radius=100000&type=all",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["results"]["results"]:
            # Ignore locations which are embedded within a Myer department store.
            if " MYER " in location["name"].upper():
                continue
            item = DictParser.parse(location)
            item["ref"] = location["identifier"]
            hours = json.loads(location["trading_hours"])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(str(hours))
            yield item
