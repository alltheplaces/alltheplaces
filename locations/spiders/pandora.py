# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_ldjson


class PandoraSpider(scrapy.spiders.SitemapSpider):
    name = "pandora"
    brand = Brand.from_wikidata("Pandora", "Q2241604")
    download_delay = 0.2
    allowed_domains = ["pandora.net"]
    sitemap_urls = ["https://stores.pandora.net/sitemap.xml"]

    def parse(self, response):
        for item in extract_ldjson(self.brand, response, "JewelryStore"):
            if item.has_geo():
                yield item
            else:
                self.logger.warn(">>>> no position for %s", response.url)
