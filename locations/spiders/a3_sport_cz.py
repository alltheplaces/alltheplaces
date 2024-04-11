import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class A3SportCZSpider(Spider):
    name = "a3_sport_cz"
    item_attributes = {"brand": "A3 Sport", "brand_wikidata": "Q58170961"}
    allowed_domains = ["www.a3sport.cz"]
    start_urls = ["https://www.a3sport.cz/prodejny?type=json&ver=1"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["name"] = location["name"].replace(", ", " ")
            item["lat"], item["lon"] = location["coordinatesGoogleMap"].split(",")
            if location["workingHoursObject"]:
                item["opening_hours"] = OpeningHours()
                opening_hours = json.loads(location["workingHoursObject"])
                for day, hours in opening_hours.items():
                    item["opening_hours"].add_range(day, hours["from"], hours["to"], "%H:%M:%S")

            yield item
