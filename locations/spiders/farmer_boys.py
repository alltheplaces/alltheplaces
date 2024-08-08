import json
import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class FarmerBoysSpider(scrapy.Spider):
    name = "farmer_boys"
    item_attributes = {"brand": "Farmer Boys", "brand_wikidata": "Q5435711"}
    allowed_domains = ["farmerboys.com"]
    start_urls = ["https://www.farmerboys.com/locations/"]

    def parse(self, response):
        locations_js = response.xpath('//script[contains(text(), "initMap")]/text()').extract_first()
        locations = re.findall(r"var\s+locations\s*=\s*(\[.*\]);", locations_js)[0]
        locations = json.loads(locations)
        for location in locations:
            properties = {
                "name": location["location_name"],
                "ref": location["location_url"],
                "street_address": location["address_1"],
                "city": location["city"],
                "postcode": location["postal_code"],
                "state": location["state"],
                "country": "US",
                "phone": location["phone"],
                "website": "https://www.farmerboys.com/locations/location-detail.php?loc="
                + location["location_url"].strip(),
                "image": (
                    "https://www.farmerboys.com/images/locations/" + location["location_pic"].strip()
                    if location["location_pic"]
                    else None
                ),
                "lat": float(location["lat"]) if location["lat"] else None,
                "lon": float(location["lng"]) if location["lng"] else None,
            }

            oh = OpeningHours()

            for days, open_time, close_time in re.findall(
                r"(\w+-\w+|\w+)<span>([\d:ap]+)-([\d:ap]+)", location["location_hours"]
            ):
                open_time = open_time.replace("a", "AM").replace("p", "PM")
                close_time = close_time.replace("a", "AM").replace("p", "PM")

                days = days.replace("Thru", "Th")

                if "-" in days:
                    start_day, end_day = days.split("-")

                    start_day = sanitise_day(start_day)
                    end_day = sanitise_day(end_day)

                    for day in day_range(start_day, end_day):
                        oh.add_range(day, open_time, close_time, time_format="%I:%M%p")
                else:
                    oh.add_range(days, open_time, close_time, time_format="%I:%M%p")

            properties["opening_hours"] = oh.as_opening_hours()

            yield Feature(**properties)
