from typing import AsyncIterator

import pycountry
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class JiffyLubeUSSpider(Spider):
    name = "jiffy_lube_us"
    item_attributes = {"brand": "Jiffy Lube", "brand_wikidata": "Q6192247"}
    allowed_domains = ["www.jiffylube.com"]
    start_urls = ["https://www.jiffylube.com/accel/locations/search/state/##"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            for state in pycountry.subdivisions.get(country_code="US"):
                yield JsonRequest(url=url.replace("##", state.code[-2:]))

    def parse(self, response):
        for location in response.json()["locations"]:
            if not location.get("is_open"):
                continue
            item = DictParser.parse(location)
            item["name"] = location.get("nickname")
            item["street_address"] = item.pop("addr_full")
            if item.get("postcode"):
                item["postcode"] = item.get("postcode").strip()
            item["phone"] = location.get("phone_main")
            if location.get("_links") and location["_links"].get("_self"):
                item["website"] = "https://www.jiffylube.com" + location["_links"]["_self"]
            item["opening_hours"] = OpeningHours()
            for day in location["hours_schema"]:
                if day["name"] in DAYS_FULL and day["time_open"] != day["time_close"]:
                    item["opening_hours"].add_range(day["name"], day["time_open"], day["time_close"])
            yield item
