# -*- coding: utf-8 -*-
import scrapy

from locations.brands import Brand
from locations.seo import extract_ldjson
from locations.hours import OpeningHours


class ClairesSpider(scrapy.spiders.SitemapSpider):
    name = "claires"
    brand = Brand.from_wikidata("Claire's", "Q2974996")
    allowed_domains = ["claires.com"]
    sitemap_urls = ["https://stores.claires.com/sitemap.xml"]
    sitemap_rules = [(".html", "parse_store")]

    def parse_store(self, response):
        for item in extract_ldjson(self.brand, response, "JewelryStore"):
            if item.has_geo():
                hours = self.parse_hours(item["source_data"]["ld_json"]["openingHours"])
                if hours:
                    item["opening_hours"] = hours
                yield item
            else:
                self.logger.warn("no location for: %s", response.url)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = hours.replace(" - ", " ")
        hours = hours.split(" ")

        if len(hours) == 22:
            for idx, val in enumerate(hours):
                if idx in (0, 3, 6, 9, 12, 15, 18):
                    day = val
                if idx in (1, 4, 7, 10, 13, 16, 19):
                    start = val
                if idx in (2, 5, 8, 11, 14, 17, 20):
                    end = val

                    opening_hours.add_range(day=day, open_time=start, close_time=end)

        return opening_hours.as_opening_hours()
