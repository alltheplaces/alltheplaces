import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser

KFC_SHARED_ATTRIBUTES = {"brand": "KFC", "brand_wikidata": "Q524757"}


class KFCSpider(scrapy.spiders.SitemapSpider):
    name = "kfc"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = [
        "https://www.kfc.co.uk/sitemap.xml",
        "https://locations.kfc.com/sitemap.xml",
    ]
    download_delay = 0.5

    def _parse_sitemap(self, response):
        def follow_link(url):
            if "kfc.co.uk" in url:
                return "/kfc-near-me/" in url
            for s in ["/delivery", "/chickensandwich"]:
                if url.endswith(s):
                    return False
            return True

        for x in super()._parse_sitemap(response):
            if follow_link(x.url):
                yield x

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        for store_type in ["FoodEstablishment", "Restaurant"]:
            if item := LinkedDataParser.parse(response, store_type):
                yield item
