from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BioburgerFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bioburger_fr"
    item_attributes = {"brand": "Bioburger", "brand_wikidata": "Q139679401"}
    sitemap_urls = ["https://restaurants.bioburger.fr/robots.txt"]
    sitemap_rules = [(r"/restaurant-burger-bio/([^/]+)/$", "parse")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Bioburger ")

        apply_category(Categories.FAST_FOOD, item)
        yield item
