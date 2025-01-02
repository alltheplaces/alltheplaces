from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ShakeShackSpider(CrawlSpider, StructuredDataSpider):
    name = "shake_shack"
    download_delay = 2.0
    item_attributes = {"brand": "Shake Shack", "brand_wikidata": "Q1058722"}
    start_urls = ["https://shakeshack.com/locations"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/location/[-\w]+$"),
            callback="parse_sd",
        ),
    ]
