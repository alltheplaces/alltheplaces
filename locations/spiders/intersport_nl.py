import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class IntersportNLSKSpider(scrapy.Spider):
    name = "intersport_nl_sk"
    start_urls = ["https://www.intersport.nl/stores", "https://www.intersport.sk/stores"]

    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+storesJson\s*=\s*(\[.*?\]);"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            oh = OpeningHours()
            for day, hours in store.get("storeHours", {}).items():
                capitalized_day = day.capitalize()
                if capitalized_day not in DAYS_EN.keys():
                    continue
                oh.add_range(
                    day=DAYS_EN.get(capitalized_day),
                    open_time=hours.get("fromFirst")[:5],
                    close_time=hours.get("toFirst")[:5],
                    time_format="%H:%M",
                )
            item = DictParser.parse(store)
            item["ref"] = store.get("storeID")
            item["street_address"] = " ".join(
                filter(None, [store.get("houseNr"), store.get("houseNrAddition"), store.get("address2")])
            )
            item["website"] = store.get("link")
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["opening_hours"] = oh
            yield Feature(item)
