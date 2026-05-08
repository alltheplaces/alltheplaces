from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DirkNLSpider(CrawlSpider, StructuredDataSpider):
    name = "dirk_nl"
    item_attributes = {"brand": "Dirk", "brand_wikidata": "Q17502722"}
    start_urls = ["https://www.dirk.nl/winkels/"]
    rules = [Rule(LinkExtractor(r"/winkels/[^/]+/[^/]+/(\d+)$"), "parse")]
    wanted_types = ["GroceryStore"]
    search_for_facebook = False
    time_format = "%H:%M:%S"

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for rule in ld_data.get("openingHoursSpecification") or []:
            if d := sanitise_day(rule.get("dayOfWeek"), DAYS_NL):
                rule["dayOfWeek"] = d

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
