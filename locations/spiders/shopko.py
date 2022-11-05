import re

import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.items import GeojsonPointItem


class ShopkoSpider(scrapy.spiders.SitemapSpider):
    name = "shopko"
    item_attributes = {"brand": "Shopko Optical", "brand_wikidata": "Q109228833"}
    allowed_domains = ["shopko.com"]
    sitemap_urls = [
        "https://www.shopko.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/store-\d", "parse"),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Optometric")
        item["ref"] = re.search(r"/store-(\d+)", response.url)[1]
        yield item
