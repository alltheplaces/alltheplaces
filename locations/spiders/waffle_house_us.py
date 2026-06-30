from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WaffleHouseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "waffle_house_us"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    sitemap_urls = ["https://locations.wafflehouse.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z0-9-]+-[a-z]{2}-(\d+)/$", "parse")]
    wanted_types = ["Restaurant"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("-", 1)[-1]
        item["name"] = item["image"] = None
        apply_category(Categories.RESTAURANT, item)

        yield item
