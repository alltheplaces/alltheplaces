from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class WelcomeSpider(SitemapSpider):
    name = "welcome"
    item_attributes = {"brand": "Welcome"}
    sitemap_urls = ["https://stores.welcome-stores.co.uk/sitemap.xml"]
    sitemap_rules = [("", "parse_item")]

    def parse_item(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "GroceryStore")

        if item is None:
            return

        item["ref"] = item["website"]

        return item
