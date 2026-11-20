from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SpaWorldAUNZSpider(SitemapSpider, StructuredDataSpider):
    name = "spa_world_au_nz"
    item_attributes = {"brand": "Spa World", "brand_wikidata": "Q124003802"}
    sitemap_urls = [
        "https://www.spaworld.com.au/sitemap/sitemap-index.xml",
        "https://www.spaworld.co.nz/sitemap/sitemap-index.xml",
    ]
    sitemap_rules = [(r"/find-a-showroom/[^/]+/[^/]+/?$", "parse")]
    wanted_types = ["HotTubStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = None
        item["branch"] = item.pop("name").removeprefix("Spa World ").strip("- ")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_SWIMMING_POOL, item)

        yield item
