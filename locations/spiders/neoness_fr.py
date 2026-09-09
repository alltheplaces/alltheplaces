from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NeonessFRSpider(SitemapSpider, StructuredDataSpider):
    name = "neoness_fr"
    item_attributes = {"brand": "Neoness", "brand_wikidata": "Q86668014"}
    sitemap_urls = ["https://www.neoness.fr/robots.txt"]
    sitemap_rules = [("/clubs/", "parse_sd")]
    drop_attributes = {"image"}
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Neoness ")
        apply_category(Categories.GYM, item)
        yield item
