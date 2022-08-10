# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class CostcutterGBSpider(scrapy.spiders.SitemapSpider):
    name = "costcutter_gb"
    item_attributes = {
        "brand": "Costcutter",
        "brand_wikidata": "Q5175072",
    }
    allowed_domains = ["costcutter.co.uk"]
    sitemap_urls = ["https://store-locator.costcutter.co.uk/sitemap.xml"]
    sitemap_rules = [("/costcutter-*", "parse_store")]

    def parse_store(self, response):
        ld = LinkedDataParser.find_linked_data(response, "ConvenienceStore")
        if ld:
            ld["brand"] = None
            return LinkedDataParser.parse_ld(ld)
