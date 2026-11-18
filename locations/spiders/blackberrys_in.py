from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BlackberrysINSpider(CrawlSpider, StructuredDataSpider):
    name = "blackberrys_in"
    item_attributes = {"brand": "Blackberrys", "brand_wikidata": "Q4922570"}
    start_urls = ["https://stores.blackberrys.com/"]
    rules = [Rule(LinkExtractor(r"page=\d+$")), Rule(LinkExtractor("/Home"), callback="parse_sd")]
    wanted_types = ["Store"]
    time_format = "%I:%M %p"

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # The page has two Store nodes; only the last has openingHoursSpecification
        yield from list(super().iter_linked_data(response))[-1:]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("email", None)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
