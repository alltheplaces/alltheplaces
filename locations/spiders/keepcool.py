from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KeepcoolSpider(SitemapSpider, StructuredDataSpider):
    name = "keepcool"
    item_attributes = {"brand": "KeepCool", "brand_wikidata": "Q100146251"}
    sitemap_urls = ["https://www.keepcool.fr/sitemap.xml"]
    sitemap_rules = [("/clubs/salle-de-sport-", "parse_sd")]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.GYM, item)
        yield item
