# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class McDonaldsPTSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_pt"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse")]

    def parse(self, response):
        return LinkedDataParser.parse(response, "FastFoodRestaurant")
