from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MiniUStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mini_u_storage_us"
    item_attributes = {"brand": "Mini U Storage", "name": "Mini U Storage"}
    sitemap_urls = ["https://www.miniustorage.com/candee_location-sitemap.xml"]
    sitemap_rules = [(r"/location/USA/", "parse_sd")]
    wanted_types = ["SelfStorage", "LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if not item.get("street_address"):
            return
        item["branch"] = item.pop("name", "").removeprefix("Mini U Storage - ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
