from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RightMoveStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "right_move_storage_us"
    item_attributes = {"brand": "Right Move Storage", "name": "Right Move Storage"}
    sitemap_urls = ["https://www.rightmovestorage.com/public/sitemaps/right-move-storage_sitemap.xml"]
    sitemap_rules = [(r"/storage-units/[a-z-]+/[a-z-]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage", "LocalBusiness"]
    time_format = "%H:%M:%S"
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not item.get("street_address"):
            return
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = item.pop("name", "").split(" - ", 1)[-1]
        if len(item.get("state") or "") != 2:
            item["state"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
