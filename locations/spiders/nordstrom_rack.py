from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class NordstromRackSpider(SitemapSpider):
    name = "nordstrom_rack"
    item_attributes = {"brand": "Nordstrom Rack", "brand_wikidata": "Q21463374"}
    sitemap_urls = ["https://stores.nordstromrack.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.nordstromrack\.com\/\w{2}\/\w{2}\/[-\w]+\/[-\w]+$",
            "parse",
        )
    ]
    drop_attributes = {"image"}

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        return LinkedDataParser.parse(response, "ClothingStore")
