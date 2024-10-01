import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class PaversGBSpider(Spider):
    name = "pavers_gb"
    item_attributes = {
        "brand": "Pavers",
        "brand_wikidata": "Q7155843",
        "country": "GB",
    }
    allowed_domains = ["pavers.co.uk"]

    def start_requests(self):
        url_template = "https://www.pavers.co.uk/api/storeLocation/search?query={city}&location={lat},{lon}&page=1"
        for city in city_locations("GB", 10000):
            yield scrapy.Request(url_template.format(city=city["name"], lat=city["latitude"], lon=city["longitude"]))

    def parse(self, response):
        for location in response.json()["result"]["response"]["results"]:
            item = DictParser.parse(location["data"])
            if "line2" in location["data"]["address"]:
                item["street_address"] = merge_address_lines(
                    [location["data"]["address"]["line1"], location["data"]["address"]["line2"]]
                )

            hours = OpeningHours()
            for day, intervals in location["data"]["hours"].items():
                if "isClosed" in intervals:
                    continue
                for interval in intervals["openIntervals"]:
                    hours.add_range(day[:2].capitalize(), interval["start"], interval["end"])
            item["opening_hours"] = hours.as_opening_hours()
            yield item
