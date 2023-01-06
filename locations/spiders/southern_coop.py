from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class SouthernCoopSpider(SitemapSpider):
    name = "southern_coop"
    item_attributes = {"brand": "Southern Co-op", "brand_wikidata": "Q7569773"}
    sitemap_urls = ["https://stores.thesouthernco-operative.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.thesouthernco-operative\.co\.uk\/[-\w]+\/[-\w]+\/[-\w]+\.html$",
            "parse_item",
        )
    ]

    def parse_item(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "GroceryStore")

        if item is None:
            return

        item["ref"] = item["website"]

        return item
