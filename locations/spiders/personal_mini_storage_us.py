from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PersonalMiniStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "personal_mini_storage_us"
    item_attributes = {"brand": "Personal Mini Storage", "name": "Personal Mini Storage"}
    sitemap_urls = ["https://www.personalministorage.com/sitemap.xml"]
    sitemap_rules = [(r"/storage-units-near-me/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    time_format = "%I:%M %p"
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url
        item["country"] = "US"
        item.pop("name", None)
        item["branch"] = item["street_address"]
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
