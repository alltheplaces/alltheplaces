
import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HandelsbankenGBSpider(scrapy.Spider):
    name = "handelsbanken_gb"
    item_attributes = {"brand": "Handelsbanken", "brand_wikidata": "Q1421630"}
    start_urls = ["https://www.handelsbanken.co.uk/rsoia/parg/bu/branches/v3/country/GB/en"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = "Handelsbanken"
            item["branch"] = location["name"]
            item["website"] = "https://" + location["branchUrl"]
            item["street_address"] = location["streetAddress"]

            oh = OpeningHours()
            days = location["openingHours"]
            for day in days:
                oh.add_range(DAYS[int(day.get("weekday"))], day.get("openTime"), day.get("closeTime"))
            item["opening_hours"] = oh.as_opening_hours()

            yield item
