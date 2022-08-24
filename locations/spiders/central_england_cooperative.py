from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class CentralEnglandCooperativeSpider(SitemapSpider):
    name = "central_england_cooperative"
    item_attributes = {
        "brand": "Central England Co-operative",
        "brand_wikidata": "Q16986583",
    }
    sitemap_urls = ["https://stores.centralengland.coop/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.centralengland\.coop\/[-\w]+\/.*$",
            "parse_item",
        )
    ]

    def parse_item(self, response):
        MicrodataParser.convert_to_json_ld(response)
        return LinkedDataParser.parse(response, "LocalBusiness")
