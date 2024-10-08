import json
import re

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DuluthTradingSpider(CrawlSpider):
    name = "duluth_trading"
    item_attributes = {"brand": "Duluth Trading", "brand_wikidata": "Q48977107"}
    allowed_domains = ["duluthtrading.com"]
    start_urls = ["https://www.duluthtrading.com/our-stores"]
    rules = [Rule(LinkExtractor(allow="/locations/"), callback="parse", follow=True)]

    def parse(self, response):
        url = "https://www.duluthtrading.com/mobify/proxy/ocapi/s/DTC/api/store/detail/?id={}"
        id_store = re.findall("[0-9]+", response.url)[0]
        yield scrapy.Request(url=url.format(id_store), method="POST", callback=self.parse_store)

    def parse_store(self, response):
        item = DictParser.parse(response.json())

        if item["email"] == "NULL":
            item["email"] = None

        days = json.loads(response.json().get("storeHoursData").replace("\n", "").replace("\t", "")).get("storeHours")
        oh = OpeningHours()
        for day in days:
            if day.get("day") == "Holidays":
                continue
            oh.add_range(
                day=day.get("day"),
                open_time=day.get("hours24format")[0],
                close_time=day.get("hours24format")[1],
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
