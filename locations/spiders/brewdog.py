import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BrewdogSpider(scrapy.Spider):
    name = "brewdog"
    item_attributes = {"brand": "BrewDog", "brand_wikidata": "Q911367"}
    allowed_domains = ["www.brewdog.com"]
    start_urls = ["https://www.brewdog.com/uk/bar-locator#ALL"]

    def parse(self, response):
        data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        data_json = json.loads(data)
        bars = data_json["props"]["pageProps"]["content"]
        for bar in bars:
            item = DictParser.parse(bar["fields"])
            item["ref"] = bar["sys"]["id"]
            opening_hours = bar["fields"].get("openingHours")
            oh = OpeningHours()
            if opening_hours:
                for key, value in opening_hours.items():
                    if key == "exceptions" or value.get("is_open") is False:
                        continue
                    oh.add_range(
                        day=key,
                        open_time=value.get("open"),
                        close_time=value.get("close"),
                    )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
