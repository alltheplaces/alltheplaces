from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class StoreRocketSpider(Spider):
    dataset_attributes = {"source": "api", "api": "storerocket.io"}

    storerocket_id = ""
    base_url = None

    def start_requests(self):
        yield JsonRequest(url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations")

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))

            item["facebook"] = location.get("facebook")
            item["extras"]["instagram"] = location.get("instagram")
            item["twitter"] = location.get("twitter")

            if self.base_url:
                item["website"] = f'{self.base_url}?location={location["slug"]}'

            item["opening_hours"] = OpeningHours()
            for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                if not location[day]:
                    continue
                hour_ranges = location[day].split(",")
                for hour_range in hour_ranges:
                    open_time = hour_range.split("-")[0].strip()
                    close_time = hour_range.split("-")[1].strip()
                    item["opening_hours"].add_range(DAYS_EN[day.title()], open_time, close_time)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
