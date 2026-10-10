import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GioninosPizzeriaUSSpider(scrapy.Spider):
    name = "gioninos_pizzeria_us"
    item_attributes = {"brand": "Gionino's Pizzeria", "brand_wikidata": "Q115238201", "country": "US"}
    allowed_domains = ["www.gioninos.com"]
    start_urls = ["https://www.gioninos.com/Locations/GetAllLocations"]

    def parse(self, response):
        for location in response.json():
            yield scrapy.Request(
                f"https://www.gioninos.com/Locations/GetPreferredLocationDetails?LocationId={location['LocationId']}",
                callback=self.parse_preferred_location_details,
            )

    def parse_preferred_location_details(self, response):
        if friendly_url := response.json().get("FriendlyUrl"):
            yield scrapy.Request(f"https://www.gioninos.com/locations/{friendly_url}", callback=self.parse_location)

    def parse_location(self, response):
        # Each location page embeds its own record (including lat/lon, not
        # available from the store-list APIs) in a "var locations = [...]" JS array.
        location = json.loads(re.search(r"var locations = (\[.*?\]);", response.text).group(1))[0]

        item = DictParser.parse(location)
        item["branch"] = location.get("ShortDescription") or location.get("Description")
        item["website"] = response.url

        apply_category(Categories.FAST_FOOD, item)

        oh = OpeningHours()
        days = response.css(".col-xs-4.col-md-3.Muli-Regular::text").getall()
        hours = response.css(".col-xs-8.col-md-6.Muli-Regular::text").getall()
        for day, time_range in zip(days, hours):
            if " - " in time_range:
                open_time, close_time = time_range.split(" - ", 1)
                oh.add_range(day.rstrip(":"), open_time.strip(), close_time.strip(), time_format="%I:%M %p")
        item["opening_hours"] = oh

        yield item
