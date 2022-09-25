# -*- coding: utf-8 -*-
import re
from urllib.parse import urlsplit, parse_qs

import scrapy

from locations.hours import OpeningHours, day_range
from locations.open_graph_parser import OpenGraphParser


class SweetTomatoesSpider(scrapy.Spider):
    name = "sweet_tomatoes"
    allowed_domains = ["sweettomatoes.co"]
    start_urls = [
        "https://sweettomatoes.co/locations/",
    ]

    def parse(self, response):
        yield from response.follow_all(xpath="//area/@href", callback=self.parse_region)

    def parse_region(self, response):
        yield from response.follow_all(
            css="div#locations a", callback=self.parse_restaurant
        )

    def parse_restaurant(self, response):
        item = OpenGraphParser.parse(response)
        [item["ref"]] = parse_qs(urlsplit(response.url).query)["store_id"]
        oh = OpeningHours()
        for hours in response.css("span.hours"):
            days = hours.xpath("./text()").get().strip(":")
            interval = hours.xpath("following-sibling::text()[1]").get()
            interval = re.sub(r"([ap])\.m\.?", r"\1m", interval)
            open_time, close_time = re.split(" (?:to|-) ", interval)
            if ":" not in open_time:
                open_time = open_time.replace(" ", ":00 ")
            if ":" not in close_time:
                close_time = close_time.replace(" ", ":00 ")
            if " - " in days or " &" in days:
                start_day, end_day = re.split(" [-&] ", days)
                for day in day_range(start_day[:2], end_day[:2]):
                    oh.add_range(day, open_time, close_time, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        item["brand"] = response.xpath(
            '//meta[@property="og:site_name"]/@content'
        ).get()
        yield item
