import scrapy

from locations.microdata_parser import MicrodataParser
from locations.linked_data_parser import LinkedDataParser


class GreatclipsSpider(scrapy.spiders.SitemapSpider):
    name = "greatclips"
    item_attributes = {"brand": "Great Clips", "brand_wikidata": "Q5598967"}
    allowed_domains = ["greatclips.com"]
    sitemap_urls = [
        "https://salons.greatclips.com/robots.txt",
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].endswith("/salon-services"):
                entry["loc"] = entry["loc"].removesuffix("/salon-services")
                yield entry

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "HealthAndBeautyBusiness")
        yield item
