import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day, DAYS_HU


class RossmannHUSpider(Spider):
    name = "rossmann_hu"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    start_urls = ["https://shop.rossmann.hu/uzletkereso"]

    def parse(self, response, **kwargs):
        data = response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get()
        data = json.loads(data)
        for store in data["props"]["pageProps"]["baseStores"]:
            item = DictParser.parse(store)
            item["postcode"] = str(item.get("postcode") or "")

            hours = store["openings"]
            oh = OpeningHours()
            for day, start_time, end_time in re.findall(r"(\w+): (\d\d:\d\d)-(\d\d:\d\d)", hours):
                day = sanitise_day(day, DAYS_HU)
                oh.add_range(day, start_time, end_time)
            item["opening_hours"] = oh

            yield item
