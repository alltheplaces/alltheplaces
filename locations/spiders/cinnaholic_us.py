from collections.abc import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CinnaholicUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cinnaholic_us"
    item_attributes = {"brand": "Cinnaholic", "brand_wikidata": "Q48965480", "extras": Categories.SHOP_BAKERY.value}
    sitemap_urls = ["https://locations.cinnaholic.com/sitemap_index.xml"]
    sitemap_rules = [(r"/ll/us/[a-z]{2}/[^/]+/\d+/$", "parse_sd")]
    wanted_types = ["Bakery"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
