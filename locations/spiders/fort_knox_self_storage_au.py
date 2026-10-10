from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FortKnoxSelfStorageAUSpider(SitemapSpider, StructuredDataSpider):
    name = "fort_knox_self_storage_au"
    item_attributes = {"brand": "Fort Knox Self Storage", "name": "Fort Knox Self Storage"}
    sitemap_urls = ["https://fortknoxselfstorage.com.au/location-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["ref"] = response.url
        item["image"] = None
        item["state"] = "VIC"
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
