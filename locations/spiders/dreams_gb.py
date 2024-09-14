import scrapy

from locations.linked_data_parser import LinkedDataParser


class DreamsGBSpider(scrapy.spiders.SitemapSpider):
    name = "dreams_gb"
    item_attributes = {
        "brand": "Dreams",
        "brand_wikidata": "Q5306688",
    }
    sitemap_urls = ["https://www.dreams.co.uk/sitemap-store.xml"]

    def parse(self, response):
        if "store-finder" not in response.url:
            return LinkedDataParser.parse(response, "FurnitureStore")
