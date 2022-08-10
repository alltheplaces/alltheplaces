# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class PandoraSpider(scrapy.spiders.SitemapSpider):
    name = "pandora"
    item_attributes = {
        "brand": "Pandora",
        "brand_wikidata": "Q2241604",
    }
    download_delay = 0.2
    allowed_domains = ["pandora.net"]
    sitemap_urls = ["https://stores.pandora.net/sitemap.xml"]
    sitemap_rules = [("\.html", "parse_store")]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "JewelryStore")
        if item:
            item["name"] = "Pandora"
            item["ref"] = response.url
            # In many countries "state" is set to "country-region", unpick and discard region
            splits = item["state"].split("-")
            if len(splits) == 2 and len(splits[0]) == 2:
                item["state"] = None
                item["country"] = splits[0]
            return item
