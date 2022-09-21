# -*- coding: utf-8 -*-
from locations.structured_data_spider import StructuredDataSpider

from scrapy.spiders import SitemapSpider


class WickesGB(SitemapSpider, StructuredDataSpider):
    name = "wickes_gb"
    item_attributes = {
        "brand": "Wickes",
        "brand_wikidata": "Q7998350",
        "country": "GB",
    }
    sitemap_urls = ["https://www.wickes.co.uk/sitemap.xml"]
    sitemap_rules = [("/store/", "parse_sd")]
    wanted_types = ["Place"]

    def inspect_item(self, item, response):
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()

        yield item
