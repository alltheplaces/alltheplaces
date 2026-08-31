from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class BurgerKingTRSpider(SitemapSpider, StructuredDataSpider):
    name = "burger_king_tr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.burgerking.com.tr/restaurants_tr.xml"]
    sitemap_rules = [(r"https://www.burgerking.com.tr/restoranlar-subeler/[^/]+/[^/]+/[^/]+/?$", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"] = response.url
        item["name"] = item["phone"] = None
        item["branch"] = response.xpath('//*[@class="current-page-name"]/text()').get("").strip()
        apply_category(Categories.FAST_FOOD, item)
        yield item
