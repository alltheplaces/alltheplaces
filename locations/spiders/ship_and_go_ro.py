from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ShipAndGoROSpider(Spider):
    name = "ship_and_go_ro"
    item_attributes = {"brand": "Ship & Go", "brand_wikidata": "Q117327750", "country": "RO"}
    start_urls = ["https://app.urgentcargus.ro/map/points?key=7f71892cbb584e0a8a1abfd487cdbf92"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["Symbol"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS:
                start_time = location.get(f"OpenHours{day}Start")
                end_time = location.get(f"OpenHours{day}End")
                if start_time and end_time:
                    item["opening_hours"].add_range(day, start_time, end_time)

            yield item
