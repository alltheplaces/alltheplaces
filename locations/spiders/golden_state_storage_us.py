from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GoldenStateStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "golden_state_storage_us"
    item_attributes = {"brand": "Golden State Storage", "name": "Golden State Storage"}
    sitemap_urls = ["https://www.goldenstatestorage.com/sitemap.xml"]
    sitemap_rules = [(r"/storage-locations/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    time_format = "%I:%M %p"
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url
        item.pop("name", None)
        item["branch"] = item["street_address"]
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
