import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class IntersportNLSKSpider(scrapy.Spider):
    name = "intersport_nl_sk"
    start_urls = ["https://www.intersport.nl/stores", "https://www.intersport.sk/stores"]
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+storesJson\s*=\s*(\[.*?\]);"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").title().removeprefix("Intersport").strip(" /")
            # Inconsistent address components, better to merge them all to make addr_full
            item.pop("street_address")
            item["addr_full"] = merge_address_lines(
                [
                    store.get("houseNr"),
                    store.get("houseNrAddition"),
                    store.get("address1"),
                    store.get("address2"),
                    store.get("storelocation"),
                ]
            )
            item["website"] = response.urljoin("/storedetail?storeID={}".format(item["ref"]))
            item["opening_hours"] = self.parse_opeing_hours(store.get("storeHours"))
            yield item

    def parse_opeing_hours(self, rules: dict) -> OpeningHours | None:
        if not rules:
            return None

        oh = OpeningHours()
        for day, time in rules.items():
            if day in ["validTo", "validFrom"]:
                continue
            for key in ["First", "Second"]:
                start_time = time.get("from{}".format(key))
                end_time = time.get("to{}".format(key))
                if start_time and end_time and len(start_time) == 5 and len(end_time) == 5:
                    oh.add_range(day, start_time, end_time)
        return oh
