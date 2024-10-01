import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class SuperdrySpider(scrapy.spiders.SitemapSpider):
    name = "superdry"
    item_attributes = {"brand": "Superdry", "brand_wikidata": "Q1684445"}
    sitemap_urls = ["https://stores.superdry.com/sitemap.xml"]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "ClothingStore")
        if item:
            yield item
    drop_attributes = {"image"}
