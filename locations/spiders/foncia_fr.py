from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FonciaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "foncia_fr"
    item_attributes = {"brand": "Foncia", "brand_wikidata": "Q1435638"}
    sitemap_urls = ["https://fr.foncia.com/agence-immobiliere.xml"]
    sitemap_rules = [(r"/agence-immobiliere/[^/]+/agence-immobiliere/[^/]+-(\d+)$", "parse_sd")]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
