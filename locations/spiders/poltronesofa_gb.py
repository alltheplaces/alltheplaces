from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PoltronesofaGBSpider(SitemapSpider, StructuredDataSpider):
    name = "poltronesofa_gb"
    item_attributes = {"brand": "Poltronesofà", "brand_wikidata": "Q80833069"}
    sitemap_urls = ["https://www.poltronesofa.co.uk/robots.txt"]
    sitemap_rules = [(r"/stores/(.+)\.html$", "parse")]
    wanted_types = ["Store"]
    custom_settings = {"REDIRECT_ENABLED": False}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("poltronesofà ")
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
