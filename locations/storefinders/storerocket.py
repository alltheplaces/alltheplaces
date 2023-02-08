from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class StorerocketSpider(Spider):
    id = ""

    def start_requests(self):
        yield JsonRequest(url=f"https://storerocket.io/api/user/{self.id}/locations")

    def parse(self, response, **kwargs):
        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))

            item["facebook"] = location.get("facebook")
            item["extras"]["instagram"] = location.get("instagram")
            item["twitter"] = location.get("twitter")

            item["opening_hours"] = OpeningHours()
            for day, times in location["hours"].items():
                day = sanitise_day(day)
                if day and times:
                    start_time, end_time = times.split("-")
                    item["opening_hours"].add_range(day, start_time, end_time)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
