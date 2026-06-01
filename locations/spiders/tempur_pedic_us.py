from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TempurPedicUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tempur_pedic_us"
    item_attributes = {"brand": "Tempur-Pedic", "brand_wikidata": "Q1756920"}
    sitemap_urls = ["https://www.tempurpedic.com/robots.txt"]
    sitemap_rules = [("/tempur-pedic-stores/tempur-pedic-", "parse")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Tempur-Pedic ")
        apply_category(Categories.SHOP_BED, item)
        yield item
