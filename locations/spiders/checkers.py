import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class CheckersSpider(scrapy.spiders.SitemapSpider):
    name = "checkers"
    item_attributes = {
        "brand": "Checkers",
        "brand_wikidata": "Q3419341",
    }
    allowed_domains = ["checkers.com"]
    sitemap_urls = [
        "https://locations.checkers.com/robots.txt",
    ]
    sitemap_rules = [(r"^https://locations\.checkers\.com/[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FastFoodRestaurant")
        yield item
