from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BigmatBESpider(SitemapSpider, StructuredDataSpider):
    name = "bigmat"
    item_attributes = {"brand": "BigMat", "brand_wikidata": "Q101851862"}
    sitemap_urls = ["https://magasins.bigmat.be/sitemap.xml", "https://magasins.bigmat.fr/sitemap.xml"]
    sitemap_rules = [("/bigmat-", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("BigMat ", "")
        apply_category(Categories.SHOP_TRADE, item)
        yield item
