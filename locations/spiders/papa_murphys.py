from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class PapaMurphysSpider(SitemapSpider):
    name = "papa_murphys"
    item_attributes = {"brand": "Papa Murphy's", "brand_wikidata": "Q7132349"}
    allowed_domains = ["papamurphys.com"]
    sitemap_urls = ["https://locations.papamurphys.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"^https://locations.papamurphys.com/[^/]+/[^/]+/[^/]+?",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FoodEstablishment")
        yield item
