from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CabinetBedinFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cabinet_bedin_fr"
    item_attributes = {"brand": "Cabinet Bedin", "brand_wikidata": "Q141309660"}
    sitemap_urls = ["https://www.cabinet-bedin.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.cabinet-bedin.com/agence-immobiliere/.*", "parse_sd")]
    wanted_types = ["RealEstateAgent"]
    drop_attributes = {"image", "email"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Cabinet Bedin Immobilier ")

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
