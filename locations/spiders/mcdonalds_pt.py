# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsPTSpider(scrapy.spiders.SitemapSpider):
    name = "mcdonalds_pt"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse")]

    def parse(self, response):
        return LinkedDataParser.parse(response, "FastFoodRestaurant")
