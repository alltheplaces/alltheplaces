import collections

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SpecsaversNZSpider(CrawlSpider):
    name = "specsavers_nz"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.co.nz/stores/full-store-list"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.specsavers\.co\.nz\/stores\/(?!full-store-list)((?!<\/)(.(?!-hearing))+)$"
            ),
            callback="parse_store_page",
        )
    ]

    def parse_store_page(self, response):
        url = response.xpath("//div/@data-yext-url").get()
        yield scrapy.Request(url, self.parse_yext_data, meta={"website": response.url})

    def parse_yext_data(self, response):
        location = response.json()["response"]
        item = DictParser.parse(location)
        item["name"] = location["locationName"]
        item["street_address"] = location["address"]
        if "address2" in location:
            item["street_address"] = item["street_address"] + ", " + location["address2"]
        item.pop("state")
        item["website"] = response.meta["website"]
        oh = OpeningHours()
        hours_ranges = location["hours"].split(",")
        day_list = collections.deque(DAYS.copy())
        day_list.rotate(1)
        for hours_range in hours_ranges:
            parts = hours_range.split(":")
            oh.add_range(day_list[int(parts[0]) - 1], f"{parts[1]}:{parts[2]}", f"{parts[3]}:{parts[4]}")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
