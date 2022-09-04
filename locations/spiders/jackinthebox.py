import scrapy
from locations.microdata_parser import MicrodataParser
from locations.linked_data_parser import LinkedDataParser


class JackInTheBoxSpider(scrapy.spiders.SitemapSpider):
    name = "jackinthebox"
    item_attributes = {"brand": "Jack In The Box", "brand_wikidata": "Q1538507"}
    sitemap_urls = ["https://locations.jackinthebox.com/sitemap.xml"]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        yield LinkedDataParser.parse(response, "FastFoodRestaurant")
