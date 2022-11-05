import scrapy

from locations.linked_data_parser import LinkedDataParser


class DaveAndBustersSpider(scrapy.spiders.SitemapSpider):
    name = "dave_and_busters"
    item_attributes = {
        "brand": "Dave and Busters",
        "brand_wikidata": "Q5228205",
    }
    allowed_domains = ["daveandbusters.com"]
    sitemap_urls = [
        "https://www.daveandbusters.com/robots.txt",
    ]
    sitemap_rules = [(r"/locations/", "parse")]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")
        yield item
