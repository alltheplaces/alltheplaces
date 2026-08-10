import re
from urllib.parse import unquote

from requests import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ChipotleSpider(CrawlSpider, StructuredDataSpider):
    name = "chipotle"
    item_attributes = {"brand": "Chipotle", "brand_wikidata": "Q465751"}

    start_urls = [
        "https://locations.chipotle.com/",
        "https://locations.chipotle.ca/",
        "https://locations.chipotle.co.uk/",
        "https://locations.chipotle.fr/",
        "https://locations.chipotle.de/",
    ]
    rules = [
        Rule(LinkExtractor(restrict_xpaths="//*[@class='mb-4']")),
        Rule(LinkExtractor(allow=r"\w+/[a-z0-9-]+$", restrict_xpaths="//*[@class='mb-4']")),
        Rule(LinkExtractor(allow=r"../[^/]+/[^/]+/[a-z-0-9]+"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(
            r"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)",
            unquote(response.xpath('//*[contains(text(),"latitude")]/text()').get()),
        ).groups()
        yield item
