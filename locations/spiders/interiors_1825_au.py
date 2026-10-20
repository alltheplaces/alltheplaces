from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Interiors1825AUSpider(SitemapSpider, StructuredDataSpider):
    name = "interiors_1825_au"
    item_attributes = {"brand": "1825 Interiors", "brand_wikidata": "Q111080640"}
    sitemap_urls = ["https://www.1825interiors.com.au/sitemap.xml"]
    sitemap_follow = [r"/sitemap_pages_"]
    sitemap_rules = [(r"/pages/", "parse_sd")]
    wanted_types = ["FurnitureStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # The "/pages/contact" page carries FurnitureStore markup for the head
        # office/warehouse, which is not a public retail store.
        if "Head Office" in item["name"]:
            return

        item["branch"] = item.pop("name").removeprefix("1825 Interiors").strip(" -")
        apply_category(Categories.SHOP_FURNITURE, item)

        # The only image present is a generic brand logo shared across every store.
        item["image"] = None

        yield item
