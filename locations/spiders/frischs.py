# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser


class FrischsSpider(scrapy.spiders.SitemapSpider):
    name = "frischs"
    item_attributes = {
        "brand": "Frisch's Big Boy",
        "brand_wikidata": "Q5504660",
    }
    allowed_domains = ["locations.frischs.com"]
    sitemap_urls = [
        "https://locations.frischs.com/sitemap.xml",
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")
        yield item
