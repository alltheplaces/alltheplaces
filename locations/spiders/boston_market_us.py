from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BostonMarketUSSpider(CrawlSpider, StructuredDataSpider):
    name = "boston_market_us"
    item_attributes = {"brand": "Boston Market", "brand_wikidata": "Q603617"}
    start_urls = ["https://www.bostonmarket.com/order"]
    rules = [Rule(LinkExtractor(r"/bm(\d+)$"), "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
