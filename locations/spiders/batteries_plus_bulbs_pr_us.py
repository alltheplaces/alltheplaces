from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BatteriesPlusBulbsPRUSSpider(CrawlSpider, StructuredDataSpider):
    name = "batteries_plus_bulbs_pr_us"
    item_attributes = {"brand": "Batteries Plus Bulbs", "brand_wikidata": "Q17005157"}
    start_urls = ["https://www.batteriesplus.com/store-locator"]
    rules = [
        Rule(LinkExtractor(allow=r"/store-locator/\w+$")),
        Rule(LinkExtractor(allow=r"/store-locator/\w+/[a-z-]+$")),
        Rule(LinkExtractor(allow=r"/store-locator/\w+/[a-z-]+/[a-z-]+\d+$"), callback="parse_sd"),
    ]
    wanted_types = ["ElectronicsStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Check us out in ", "")
        yield item
