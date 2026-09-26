import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FonciaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "foncia_fr"
    item_attributes = {"brand": "Foncia", "brand_wikidata": "Q1435638"}
    sitemap_urls = ["https://fr.foncia.com/agence-immobiliere.xml"]
    sitemap_rules = [(r"/agence-immobiliere/[^/]+/agence-immobiliere/[^/]+-(\d+)$", "parse_sd")]
    wanted_types = ["RealEstateAgent"]
    drop_attributes = {"facebook", "twitter"}

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for rule in ld_data.get("openingHoursSpecification") or []:
            days = rule.get("dayOfWeek")
            if isinstance(days, str):
                days = [days]
            rule["dayOfWeek"] = [sanitise_day(day, DAYS_FR) for day in days or []]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if re.match(r"foncia\b", item["name"], flags=re.IGNORECASE):
            item["branch"] = item.pop("name")[len("foncia") :].strip(" -")
        item["website"] = response.url
        if "agence-default-photo" in (item.get("image") or ""):
            item.pop("image")
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
