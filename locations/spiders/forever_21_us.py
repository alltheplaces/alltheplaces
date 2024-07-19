import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class Forever21USSpider(scrapy.spiders.SitemapSpider):
    name = "forever_21_us"
    item_attributes = {
        "brand": "Forever 21",
        "brand_wikidata": "Q1060537",
    }
    allowed_domains = ["forever21.com"]
    sitemap_urls = [
        "https://locations.forever21.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/stores/", "parse"),
    ]

    def parse(self, response):
        for city in response.css('[itemprop="address"] .Address-city'):
            city.root.set("itemprop", "addressLocality")
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "ClothingStore")
        yield item
