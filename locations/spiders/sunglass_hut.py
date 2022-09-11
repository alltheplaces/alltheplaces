# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class SunglassHutSpider(scrapy.spiders.SitemapSpider):
    name = "sunglass_hut"
    item_attributes = {"brand": "Sunglass Hut", "brand_wikidata": "Q136311"}
    allowed_domains = ["stores.sunglasshut.com"]
    sitemap_urls = [
        "https://stores.sunglasshut.com/robots.txt",
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        ld = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        if ld is None:
            return

        ld["geo"] = ld["geo"][0]
        item = LinkedDataParser.parse_ld(ld)
        yield item
