# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class ClairesSpider(scrapy.spiders.SitemapSpider):
    name = "claires"
    item_attributes = {"brand": "Claire's", "brand_wikidata": "Q2974996"}
    allowed_domains = ["claires.com"]
    sitemap_urls = ["https://stores.claires.com/sitemap.xml"]
    sitemap_rules = [(".html", "parse_store")]
    download_delay = 0.2

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "JewelryStore")
        if item:
            item["ref"] = response.url
            # Once again (see Pandora) a site that wishes to encode country-state into the state field
            if item["state"] == "JE":
                item["state"] = "JE-JerseyIsSpecial"
            splits = item["state"].split("-")
            if len(splits) == 2 and len(splits[0]) == 2:
                item["state"] = None
                item["country"] = splits[0]
            return item
