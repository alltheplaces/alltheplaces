# -*- coding: utf-8 -*-
import scrapy
import re

from locations.linked_data_parser import LinkedDataParser


class FamousFootwearSpider(scrapy.spiders.SitemapSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://www.famousfootwear.com/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse")]
    download_delay = 2.0
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Store")
        item["ref"] = item["website"]
        pattern = re.compile('location: \["(.*)", "(.*)"\],')
        matches = pattern.search(response.text)
        item["lat"], item["lon"] = matches.group(1), matches.group(2)
        yield item
