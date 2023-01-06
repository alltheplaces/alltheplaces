from urllib.parse import urlparse

import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class DelTacoSpider(scrapy.spiders.SitemapSpider):
    name = "deltaco"
    item_attributes = {
        "brand": "Del Taco",
        "brand_wikidata": "Q1183818",
    }

    allowed_domains = ["locations.deltaco.com"]
    sitemap_urls = [
        "https://locations.deltaco.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"https://locations\.deltaco\.com/[^e].+\/.+\/.+\/.+", "parse"),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FastFoodRestaurant")
        item["city"] = response.css(".Address-field.Address-city::text").get()
        item["country"] = urlparse(response.url).path.split("/", 2)[1].upper()
        yield item
