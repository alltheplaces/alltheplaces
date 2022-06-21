# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_ldjson


class CostcutterUKSpider(scrapy.spiders.SitemapSpider):
    name = "costcutter_uk"
    brand = Brand.from_wikidata("Costcutter", "Q5175072")
    allowed_domains = ["costcutter.co.uk"]
    sitemap_urls = ["https://store-locator.costcutter.co.uk/sitemap.xml"]
    sitemap_rules = [("/costcutter-*", "parse_store")]

    def parse_store(self, response):
        return extract_ldjson(self.brand, response, "ConvenienceStore")
