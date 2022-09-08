# -*- coding: utf-8 -*-
import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SamsClubSpider(scrapy.spiders.SitemapSpider):
    name = "sams_club"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}
    allowed_domains = ["www.samsclub.com"]
    sitemap_urls = [
        "https://www.samsclub.com/sitemap_locators.xml",
    ]

    def parse(self, response):
        [script] = filter(
            lambda script: "clubDetails" in script,
            response.xpath('//script[@type="application/json"]/text()').extract(),
        )
        data = json.loads(script)["clubDetails"]
        item = DictParser.parse(data)
        item["website"] = response.url
        oh = OpeningHours()
        for day, interval in data["operationalHours"].items():
            oh.add_range(day[:2].title(), interval["startHrs"], interval["endHrs"])
        item["opening_hours"] = oh.as_opening_hours()
        yield item
