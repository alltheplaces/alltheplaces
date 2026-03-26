from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ShipAndGoROSpider(Spider):
    name = "ship_and_go_ro"
    item_attributes = {"brand": "Ship & Go", "brand_wikidata": "Q117327750", "country": "RO"}
    start_urls = ["https://www.cargus.ro/wp-content/plugins/find-ship-go-cargus/data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
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
