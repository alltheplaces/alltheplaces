import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GantSpider(Spider):
    name = "gant"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    start_urls = [
        "https://www.gant.dk/store-locator",
        "https://www.gant.be/nl-be/store-locator",
        "https://www.gant.at/store-locator",
        "https://www.gant.fr/store-locator",
        "https://www.gant.co.uk/store-locator",
        "https://www.gant.pt/store-locator",
        "https://www.gant.es/store-locator",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(re.search(r"data\":(\[.*?\]),\"offset", response.text).group(1))
        if raw_data:
            for location in raw_data:
                item = DictParser.parse(location)
                if location.get("address2"):
                    item["street_address"] = merge_address_lines(
                        [
                            location.get("address2"),
                            item["street_address"],
                        ]
                    )
                try:
                    oh = OpeningHours()
                    for day, time in json.loads(location["storeHours"]).items():
                        if day == "holidayHours":
                            continue
                        if time.get("isClosed"):
                            oh.set_closed(day)
                        else:
                            for open_close_time in time["openIntervals"]:
                                open_time = open_close_time["start"]
                                close_time = open_close_time["end"]
                                oh.add_range(day=day, open_time=open_time, close_time=close_time)
                    item["opening_hours"] = oh
                except:
                    pass
                yield item
