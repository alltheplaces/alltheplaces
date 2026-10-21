from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FriendlysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "friendlys_us"
    item_attributes = {"brand": "Friendly's", "brand_wikidata": "Q1464513"}
    sitemap_urls = ["https://locations.friendlysrestaurants.com/sitemap.xml"]
    sitemap_rules = [(r"/ll/us/[a-z]{2}/[^/]+/[^/]+/$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("image", None)
        yield item
