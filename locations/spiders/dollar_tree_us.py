from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DollarTreeUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dollar_tree_us"
    item_attributes = {"brand": "Dollar Tree", "brand_wikidata": "Q5289230"}
    sitemap_urls = ["https://locations.dollartree.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse")]
    wanted_types = ["Store"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
