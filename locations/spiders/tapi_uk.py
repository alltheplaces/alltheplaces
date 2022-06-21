# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_ldjson


class TapiUKSpider(scrapy.spiders.SitemapSpider):
    name = "tapi_uk"
    brand = Brand.from_wikidata("Tapi", "Q79223951")
    allowed_domains = ["tapi.co.uk"]
    sitemap_urls = ["https://www.tapi.co.uk/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_store")]

    def parse_store(self, response):
        return extract_ldjson(self.brand, response, "HomeGoodsStore")
