# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class UrbanOutfitters(SitemapSpider, StructuredDataSpider):
    download_delay = 0.1
    name = "thecheesecakefactory"
    item_attributes = {"brand": "The Cheesecake Factory", "brand_wikidata": "Q1045842"}
    allowed_domains = [
        "www.thecheesecakefactory.com",
        "locations.thecheesecakefactory.com",
    ]
    sitemap_urls = ["https://locations.thecheesecakefactory.com/robots.txt"]
    sitemap_rules = [("", "parse_sd")]
