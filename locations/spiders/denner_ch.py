from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class DennerCHSpider(SitemapSpider, StructuredDataSpider):
    name = "denner_ch"
    item_attributes = {"brand": "Denner", "brand_wikidata": "Q379911"}
    sitemap_urls = ["https://www.denner.ch/sitemap.store.xml"]
    sitemap_rules = [("/de/filialen/", "parse_sd")]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if isinstance(ld_obj.get("@graph"), list):
                ld_obj = ld_obj["@graph"][0]

            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj

    def pre_process_data(self, ld_data: dict, **kwargs):
        for index, rule in enumerate(
            ld_data.get("openingHoursSpecification", [])
        ):  # Actual hours starts from Monday, but raw data wrongly starts from Tuesday
            rule["dayOfWeek"] = DAYS_FULL[index]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = ld_data["name"].removesuffix(" Filiale")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
