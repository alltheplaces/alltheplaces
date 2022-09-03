# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


class AshleyFurnitureSpider(scrapy.spiders.SitemapSpider):
    name = "ashley_furniture"
    item_attributes = {"brand": "Ashley Furniture", "brand_wikidata": "Q4805437"}
    sitemap_urls = ["https://stores.ashleyfurniture.com/sitemap_index.xml"]
    sitemap_rules = [("/store/", "parse_store")]
    download_delay = 1.0

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "FurnitureStore")
        if item:
            item["ref"] = response.url
            yield item
