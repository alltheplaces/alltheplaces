import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class BonefishGrillSpider(scrapy.spiders.SitemapSpider):
    name = "bonefish_grill"
    item_attributes = {
        "brand": "Bonefish Grill",
        "brand_wikidata": "Q4941599",
    }
    allowed_domains = ["bonefishgrill.com"]
    sitemap_urls = [
        "https://locations.bonefishgrill.com/robots.txt",
    ]
    sitemap_rules = [
        (r"https://locations\.bonefishgrill\.com/[^/]+/[^/]+/[^/]+$", "parse"),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "Restaurant")
        yield item
