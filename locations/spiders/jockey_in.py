from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JockeyINSpider(SitemapSpider, StructuredDataSpider):
    name = "jockey_in"
    item_attributes = {"brand": "Jockey", "brand_wikidata": "Q534235"}
    sitemap_urls = ["https://stores.jockey.in/sitemaps/v1/google/index-10001.xml"]
    sitemap_rules = [(r"jockey-exclusive-store-[\w\-/]+/home", "parse_sd")]
    time_format = "%I:%M %p"
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = item["name"].split("|", 1)[1].strip()
        if "stores.jockey.in" in item["facebook"] or "com/jockeyindia" in item["facebook"]:
            item["facebook"] = None
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
