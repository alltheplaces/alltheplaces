import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class TangoSpider(scrapy.Spider):
    name = "tango"
    item_attributes = {"brand": "Tango", "brand_wikidata": "Q2423920"}
    start_urls = ["https://www.tango.nl/get/stations.json"]

    def parse(self, response):
        for data in response.json().get("Stations").get("Station"):
            oh = OpeningHours()
            for day, hours in data.get("OpeningHours").items():
                start, end = hours.split("-")
                oh.add_range(day=day, open_time=start, close_time=end)
            yield Feature(
                {
                    "ref": data.get("StationId"),
                    "name": data.get("Name"),
                    "country": data.get("Country"),
                    "email": data.get("Email"),
                    "phone": data.get("Phone"),
                    "lat": data.get("XCoordinate"),
                    "lon": data.get("YCoordinate"),
                    "street_address": data.get("Address_line_1"),
                    "addr_full": " ".join([data.get("Address_line_1"), data.get("Address_line_2")]),
                    "website": f"https://www.tango.nl{data.get('NodeURL')}" if data.get("NodeURL") else None,
                    "opening_hours": oh,
                }
            )
