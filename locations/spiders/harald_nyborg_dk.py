import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, OpeningHours, sanitise_day


class HaraldNyborgDKSpider(Spider):
    name = "harald_nyborg_dk"
    item_attributes = {"brand": "Harald Nyborg", "brand_wikidata": "Q12315668"}
    start_urls = ["https://www.harald-nyborg.dk/internal/physicalshop/listAllPhysicalShops"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["physicalShops"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            day_time = location.get("openingHours")
            item["opening_hours"] = OpeningHours()
            for day, open_time, close_time in re.findall(r"<td>(\w+):</td><td>(\d+\.\d+)+\s*-\s*(\d+\.\d+)", day_time):
                day = sanitise_day(day, DAYS_DK)
                item["opening_hours"].add_range(day, open_time, close_time, time_format="%H.%M")
            yield item
