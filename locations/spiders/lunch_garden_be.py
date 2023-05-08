import html

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class LunchGardenBESpider(Spider):
    name = "lunch_garden_be"
    item_attributes = {"brand": "Lunch Garden", "brand_wikidata": "Q2491217"}
    start_urls = ["https://www.lunchgarden.be/fr/app/json"]

    def parse(self, response, **kwargs):
        for location in response.json()["restaurants"]:
            for k, v in location["restaurant"].items():
                location[k.replace("field_", "")] = v

            item = DictParser.parse(location)

            item["street_address"] = html.unescape(location["adresse_1"])
            item["addr_full"] = html.unescape(location["adresse"])

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if times := location.get(day.lower()):
                    start_time, end_time = times.split(" – ")
                    item["opening_hours"].add_range(day, start_time, end_time)

            yield item
