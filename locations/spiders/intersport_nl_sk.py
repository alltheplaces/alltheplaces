import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class IntersportNLSKSpider(scrapy.Spider):
    name = "intersport_nl_sk"
    start_urls = ["https://www.intersport.nl/stores", "https://www.intersport.sk/stores"]

    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+storesJson\s*=\s*(\[.*?\]);"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            item = DictParser.parse(store)
            item["ref"] = store.get("storeID")
            item["street_address"] = " ".join(
                filter(None, [store.get("houseNr"), store.get("houseNrAddition"), store.get("address2")])
            )
            item["website"] = store.get("link")
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["opening_hours"] = OpeningHours()
            if timing := store.get("storeHours"):
                for day, time in timing.items():
                    if day := sanitise_day(day):
                        for shift in time:
                            if "from" in shift:
                                shift_name = shift.split("from")[1]
                                open_time_match, close_time_match = [
                                    re.search(r"(\d+:\d+)", t)
                                    for t in [time[f"from{shift_name}"], time[f"to{shift_name}"]]
                                ]
                                if open_time_match and close_time_match:
                                    item["opening_hours"].add_range(
                                        day, open_time_match.group(1), close_time_match.group(1)
                                    )

            yield item
