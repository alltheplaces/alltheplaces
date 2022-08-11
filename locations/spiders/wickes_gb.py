# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class WickesGBSpider(scrapy.spiders.SitemapSpider):
    name = "wickes_gb"
    item_attributes = {
        "brand": "Wickes",
        "brand_wikidata": "Q7998350",
        "country": "GB",
    }
    sitemap_urls = ["https://www.wickes.co.uk/sitemap.xml"]
    sitemap_rules = [("/store/", "parse_store")]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Place")
        if item:
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            return item
