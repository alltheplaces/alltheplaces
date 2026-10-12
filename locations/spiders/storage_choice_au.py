from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StorageChoiceAUSpider(SitemapSpider, StructuredDataSpider):
    name = "storage_choice_au"
    item_attributes = {"brand": "Storage Choice", "name": "Storage Choice"}
    sitemap_urls = ["https://storagechoice.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https://storagechoice\.com\.au/self-storage-[^/]+$", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Storage Choice").strip()
        item["image"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
