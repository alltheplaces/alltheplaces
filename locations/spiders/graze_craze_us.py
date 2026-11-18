from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GrazeCrazeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "graze_craze_us"
    item_attributes = {"brand": "Graze Craze"}
    sitemap_urls = ["https://www.grazecraze.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_DELI, item)
        yield item
