from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day


class ZabkaPLSpider(scrapy.Spider):
    name = "zabka_pl"
    item_attributes = {"brand": "Żabka", "brand_wikidata": "Q2589061"}
    start_urls = ["https://www.zabka.pl/app/uploads/locator-store-data.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day, hours in store.get("openingHours", {}).items():
                if not hours:
                    continue
                if "-" in day:
                    start_day, end_day = day.split("-")
                else:
                    start_day = end_day = day
                start_day, end_day = sanitise_day(start_day), sanitise_day(end_day)
                if start_day and end_day:
                    open_time, close_time = hours.split("-") if "-" in hours else ("", "")
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day), open_time.strip(), close_time.strip(), time_format="%H:%M:%S"
                    )
            yield item
