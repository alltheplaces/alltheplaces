# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class BestOneGBSpider(scrapy.spiders.SitemapSpider):
    name = "bestone_gb"
    item_attributes = {"brand": "Best-one", "brand_wikidata": "Q4896532"}
    sitemap_urls = ["https://stores.best-one.co.uk/sitemap.xml"]
    download_delay = 1.0

    def parse(self, response):
        for store_type in ["ConvenienceStore", "WholesaleStore"]:
            if item := LinkedDataParser.parse(response, store_type):
                yield item
                return
