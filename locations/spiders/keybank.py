# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KeyBankSpider(SitemapSpider, StructuredDataSpider):
    name = "keybank"
    item_attributes = {"brand": "KeyBank", "brand_wikidata": "Q1740314"}
    sitemap_urls = ["https://www.key.com/about/seo.sitemap-locator.xml"]
    sitemap_rules = [(r"locations/.*/.*/.*/.*", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()
        item["name"] = response.css("h1.address__title::text").get()
        yield item
