# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


def from_wikidata(name, code):
    return {"brand": name, "brand_wikidata": code}


def set_brand(item, brand):
    item["brand"] = brand.get("brand")
    item["brand_wikidata"] = brand.get("brand_wikidata")


class MonsoonGBSpider(scrapy.spiders.SitemapSpider):
    name = "monsoon_gb"
    sitemap_urls = ["https://stores.monsoon.co.uk/sitemap.xml"]
    download_delay = 0.2
    MONSOON = from_wikidata("Monsoon", "Q65007501")
    ACCESSORIZE = from_wikidata("Accessorize", "Q65007482")
    item_attributes = {"country": "GB"}

    def parse(self, response):
        item = LinkedDataParser.parse(response, "ClothingStore")
        if item:
            item["website"] = response.url
            set_brand(item, self.MONSOON)
            yield item
            if "Accessorize" in item["name"]:
                # There is a co-located Accessorize store, this is how they work!
                item = LinkedDataParser.parse(response, "ClothingStore")
                item["website"] = response.url
                set_brand(item, self.ACCESSORIZE)
                item["ref"] += "-accessorize"
                yield item
