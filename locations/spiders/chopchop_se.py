from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ChopchopSESpider(CrawlSpider, StructuredDataSpider):
    name = "chopchop_se"
    item_attributes = {
        "brand": "ChopChop",
        "brand_wikidata": "Q104631081",
        "country": "SE",
    }
    allowed_domains = ["chopchop.se"]
    start_urls = ["https://chopchop.se/bestallonline/"]
    rules = [
        Rule(LinkExtractor(allow=r"/restaurant/[^/]+/$"), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ChopChop ")
        yield item
