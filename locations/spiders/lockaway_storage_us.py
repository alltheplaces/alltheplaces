import re
from typing import Iterable

from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LockawayStorageUSSpider(StructuredDataSpider):
    name = "lockaway_storage_us"
    item_attributes = {"brand": "Lockaway Storage", "name": "Lockaway Storage"}
    start_urls = ["https://www.lockaway-storage.com/storage-units/locations/"]
    wanted_types = ["SelfStorage", "LocalBusiness"]
    time_format = "%H:%M:%S"
    drop_attributes = {"image"}

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Request]:
        for href in set(response.css("a::attr(href)").getall()):
            if re.fullmatch(r"/storage-units/[a-z-]+/[a-z-]+/[^/]+/", href):
                yield response.follow(href, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["country"] = "US"
        item.pop("name", None)
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
