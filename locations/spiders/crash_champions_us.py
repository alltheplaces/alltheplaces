import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CrashChampionsUSSpider(scrapy.Spider):
    name = "crash_champions_us"
    item_attributes = {
        "brand_wikidata": "Q121435028",
        "brand": "Crash Champions",
    }
    start_urls = [
        "https://www.crashchampions.com/locations?view=view-all-centers",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"geoPoints\"\s*:\s*(\[.*\]),\"user\"", response.xpath('//*[contains(text(),"geoPoints")]/text()').get()
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["ref"] = location["nid"]
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.crashchampions.com" + location["alias"]
            oh = OpeningHours()
            for day_time in location.keys():
                if "openhours" in day_time:
                    day_time_string = location[day_time]
                    oh.add_ranges_from_string(day_time_string)
            item["opening_hours"] = oh
            yield item
