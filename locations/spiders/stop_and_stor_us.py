from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StopAndStorUSSpider(SitemapSpider, StructuredDataSpider):
    name = "stop_and_stor_us"
    item_attributes = {"brand": "Stop & Stor", "name": "Stop & Stor"}
    sitemap_urls = ["https://www.stopandstor.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    time_format = "%H:%M:%S"
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not item.get("street_address"):
            return
        item["ref"] = response.url
        item["branch"] = item.pop("name", None)
        item["state"] = "NY"
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
