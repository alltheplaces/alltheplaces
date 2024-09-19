from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PostieNZSpider(CrawlSpider, StructuredDataSpider):
    name = "postie_nz"
    item_attributes = {
        "brand": "Postie",
        "brand_wikidata": "Q110299434",
    }
    start_urls = ["https://www.postie.co.nz/stores/all"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.postie\.co\.nz\/store-detail\/southern\/[\w-]+"),
            callback="parse",
        ),
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.postie\.co\.nz\/store-detail\/northern\/[\w-]+"),
            callback="parse",
        ),
    ]
