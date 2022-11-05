import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class ChristmasTreeShopsSpider(scrapy.spiders.SitemapSpider):
    name = "christmas_tree_shops"
    item_attributes = {
        "brand": "Christmas Tree Shops",
        "brand_wikidata": "Q5111452",
    }
    allowed_domains = ["stores.christmastreeshops.com"]
    sitemap_urls = [
        "https://stores.christmastreeshops.com/robots.txt",
    ]
    sitemap_rules = [
        (r"https://stores\.christmastreeshops\.com/[^/]+/[^/]+/[^/]+$", "parse")
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "HomeGoodsStore")
        yield item
