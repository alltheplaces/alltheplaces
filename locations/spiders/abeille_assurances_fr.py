from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AbeilleAssurancesFRSpider(SitemapSpider, StructuredDataSpider):
    name = "abeille_assurances_fr"
    item_attributes = {"brand": "Abeille Assurances", "brand_wikidata": "Q117012137"}
    sitemap_urls = ["https://agences.abeille-assurances.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://agences\.abeille-assurances\.fr/[^/]+/?$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/AbeilleAssurances":
            item["facebook"] = None

        item["branch"] = item.pop("name").removeprefix("Agence Abeille Assurances ")

        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
