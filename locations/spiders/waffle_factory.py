from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WaffleFactorySpider(SitemapSpider, StructuredDataSpider):
    name = "waffle_factory"
    item_attributes = {"brand": "Waffle Factory", "brand_wikidata": "Q105426923"}
    sitemap_urls = ["https://restaurants.wafflefactory.com/fr/sitemap.xml"]
    sitemap_rules = [(r"/(waffle-factory-[^/]+)$", "parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item["name"].removeprefix(f"{self.item_attributes['brand']} - ").strip()
        item["image"] = None
        apply_category(Categories.FAST_FOOD, item)

        yield item
