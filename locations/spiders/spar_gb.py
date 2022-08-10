# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class SparGBSpider(scrapy.spiders.SitemapSpider):
    name = "spar_gb"
    item_attributes = {
        "brand": "SPAR",
        "brand_wikidata": "Q610492",
        "country": "GB",
    }
    download_delay = 0.2
    sitemap_urls = [
        "https://www.spar-ni.co.uk/sitemap",
        "https://www.spar.co.uk/sitemap",
    ]
    sitemap_rules = [("/store-locator*", "parse_store")]

    def parse_store(self, response):
        return LinkedDataParser.parse(response, "Store")
