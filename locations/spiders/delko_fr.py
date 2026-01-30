from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DelkoFRSpider(CrawlSpider, StructuredDataSpider):
    name = "delko_fr"
    item_attributes = {"brand": "Delko", "brand_wikidata": "Q24934757"}
    start_urls = ["https://delko.fr/garage/"]
    rules = [Rule(LinkExtractor("r/garage/delko/[^/]+/(\d+)$"), "parse")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Delko ")

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item