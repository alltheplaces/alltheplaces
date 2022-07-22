from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


class HSBCUK(CrawlSpider):
    name = "hsbc_uk"
    item_attributes = {
        "brand": "HSBC UK",
        "brand_wikidata": "Q64767453",
    }
    start_urls = ["https://www.hsbc.co.uk/branch-list/"]
    rules = [
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.hsbc\.co\.uk\/branch-list\/\/([-\w]+)$",
            ),
            callback="parse_item",
        ),
    ]

    def parse_item(self, response):
        bank = LinkedDataParser.parse(response, "Place")
        bank["ref"] = response.url
        yield bank
