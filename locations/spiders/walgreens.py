# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser


class WalgreensSpider(scrapy.spiders.SitemapSpider):
    name = "walgreens"
    sitemap_urls = ["https://www.walgreens.com/Store-Details.xml"]
    download_delay = 2.0

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Store")
        if item:
            if "/locator/walgreens-" in response.url:
                brand = ("Walgreens", "Q1591889")
            else:
                brand = ("Duane Reade", "Q5310380")
            item["brand"], item["brand_wikidata"] = brand
            yield item
