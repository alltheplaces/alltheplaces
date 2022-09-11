import scrapy

from locations.linked_data_parser import LinkedDataParser


class SnarfsSpider(scrapy.Spider):
    name = "snarfs"
    item_attributes = {"brand": "Snarf's Sandwiches", "brand_wikidata": "Q113900887"}

    allowed_domains = ["eatsnarfs.com"]
    start_urls = ("https://www.eatsnarfs.com/sitemap",)

    def parse(self, response):
        store_links = response.css(".loc-store")
        yield from response.follow_all(store_links, callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")
        if item is None:
            return
        item["ref"] = item["name"]
        yield item
