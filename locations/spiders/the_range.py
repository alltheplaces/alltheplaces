from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class TheRangeSpider(CrawlSpider, StructuredDataSpider):
    name = "the_range"
    item_attributes = {"brand": "The Range", "brand_wikidata": "Q7759409"}
    start_urls = ["https://www.therange.co.uk/stores/"]
    rules = [Rule(LinkExtractor(allow=r"/stores/\w+"), callback="parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # Wilko branded stores are collected by wilko_gb
        if "wilko" in item["name"].lower():
            return
        item["ref"] = response.url
        item["branch"] = item.pop("name").removeprefix("The Range").strip(": ")
        item.pop("facebook", None)
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
