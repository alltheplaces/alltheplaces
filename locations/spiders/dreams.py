# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_ldjson


class DreamsSpider(scrapy.spiders.SitemapSpider):
    name = "dreams"
    brand = Brand.from_wikidata("Dreams", "Q5306688")
    sitemap_urls = ["https://www.dreams.co.uk/sitemap-store.xml"]

    def parse(self, response):
        if "store-finder" not in response.url:
            return extract_ldjson(self.brand, response, "LocalBusiness")
