import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TangoSpider(scrapy.Spider):
    name = "tango"
    item_attributes = {"brand": "Tango", "brand_wikidata": "Q125867683"}
    start_urls = ["https://www.tango.nl/get/stations.json"]

    def parse(self, response):
        for data in response.json().get("Stations").get("Station"):
            item = DictParser.parse(data)
            item["ref"] = data.get("StationId")
            # Coordinates are incorrectly named in data
            item["lat"] = data.get("XCoordinate")
            item["lon"] = data.get("YCoordinate")
            item["street_address"] = data.get("Address_line_1")
            item["website"] = f"https://www.tango.nl{data.get('NodeURL')}" if data.get("NodeURL") else None
            item["addr_full"] = " ".join([data.get("Address_line_1"), data.get("Address_line_2")])
            oh = OpeningHours()
            for day, hours in data.get("OpeningHours").items():
                start, end = hours.split("-")
                oh.add_range(day=day, open_time=start, close_time=end)
            item["opening_hours"] = oh.as_opening_hours()
            apply_category(Categories.FUEL_STATION, item)
            # TODO: capture services and fuel types
            yield item
