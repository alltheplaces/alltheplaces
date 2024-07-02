import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class JacksonHewittSpider(scrapy.spiders.SitemapSpider):
    name = "jackson_hewitt"
    item_attributes = {"brand": "Jackson Hewitt", "brand_wikidata": "Q6117132"}
    allowed_domains = ["jacksonhewitt.com"]
    sitemap_urls = ["https://office.jacksonhewitt.com/sitemap.xml"]
    sitemap_rules = [
        (r"/\d+$", "parse"),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "AccountingService")
        yield item
