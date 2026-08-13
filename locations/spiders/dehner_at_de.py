from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DehnerATDESpider(SitemapSpider, StructuredDataSpider):
    name = "dehner_at_de"
    item_attributes = {"brand": "Dehner", "brand_wikidata": "Q1183029"}
    sitemap_urls = ["https://www.dehner.at/robots.txt", "https://www.dehner.de/robots.txt"]
    sitemap_rules = [("/stores/", "parse_sd")]
    wanted_types = ["GardenStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("- Dehner GC", "")
        yield item
