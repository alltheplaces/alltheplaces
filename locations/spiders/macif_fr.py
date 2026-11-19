from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MacifFRSpider(SitemapSpider, StructuredDataSpider):
    name = "macif_fr"
    item_attributes = {"brand": "Macif", "brand_wikidata": "Q3331021"}
    sitemap_urls = ["https://agences.macif.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/assurance-[^/]+/agence-[^/]+$", "parse")]
    wanted_types = ["InsuranceAgency"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = item["email"] = None
        item["branch"] = item.pop("name", None)
        item["ref"] = response.url.rstrip("/").split("-")[-1]
        apply_category(Categories.OFFICE_INSURANCE, item)

        yield item
