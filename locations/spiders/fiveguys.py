# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FiveguysSpider(scrapy.spiders.SitemapSpider):
    name = "fiveguys"
    item_attributes = {"brand": "Five Guys", "brand_wikidata": "Q1131810"}
    allowed_domains = ["restaurants.fiveguys.com"]
    sitemap_urls = ["https://restaurants.fiveguys.com/sitemap.xml"]
    sitemap_rules = [
        (
            "https://restaurants.fiveguys.com/\d*-.*$",
            "parse",
        ),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FastFoodRestaurant")
        yield item
