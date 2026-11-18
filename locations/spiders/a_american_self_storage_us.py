from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AAmericanSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "a_american_self_storage_us"
    item_attributes = {"brand": "A-American Self Storage", "name": "A-American Self Storage"}
    sitemap_urls = ["https://www.aamericanselfstorage.com/sitemap.xml"]
    sitemap_rules = [
        (r"/self-storage/[a-z]{2}/[^/]+/[^/]+$", "parse_sd"),
        (r"/\d+-[a-z0-9-]+-[a-z]{2}-\d{5}$", "parse_sd"),
    ]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("A-American Self Storage - ")
        if item["branch"] == "AAA Self Storage, LLC":
            item["branch"] = item["city"]
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
