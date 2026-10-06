from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StorageEtcUSSpider(SitemapSpider, StructuredDataSpider):
    name = "storage_etc_us"
    item_attributes = {"brand": "Storage Etc", "name": "Storage Etc"}
    sitemap_urls = ["https://www.storageetc.com/sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[a-z]{2}/[^/]+/[^/]+/?$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Storage Etc ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
