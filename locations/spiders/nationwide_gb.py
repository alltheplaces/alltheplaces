from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NationwideGB(CrawlSpider, StructuredDataSpider):
    name = "nationwide_gb"
    item_attributes = {"brand": "Nationwide", "brand_wikidata": "Q846735"}
    start_urls = ["https://www.nationwide.co.uk/branches/index.html"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"https:\/\/www\.nationwide\.co\.uk\/branches\/[-()\w]+\/[-\w]+$"
            ),
            callback="parse_sd",
        ),
        Rule(
            LinkExtractor(
                allow=r"https:\/\/www\.nationwide\.co\.uk\/branches\/[-()\w]+$"
            )
        ),
    ]
    wanted_types = ["BankOrCreditUnion"]
