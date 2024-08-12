import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class BigLotsSpider(scrapy.spiders.SitemapSpider):
    name = "big_lots"
    item_attributes = {"brand": "Big Lots", "brand_wikidata": "Q4905973"}
    allowed_domains = ["local.biglots.com"]
    sitemap_urls = [
        "https://local.biglots.com/robots.txt",
    ]
    sitemap_rules = [
        (r"https://local\.biglots\.com/[^/]+/[^/]+/[^/]+$", "parse"),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "Store")
        yield item
