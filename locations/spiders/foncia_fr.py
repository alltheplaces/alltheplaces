import re
from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FonciaFRSpider(StructuredDataSpider):
    name = "foncia_fr"
    item_attributes = {"brand": "Foncia", "brand_wikidata": "Q1435638"}
    # The agence-immobiliere.xml sitemap is stale (dead agencies, missing new
    # ones, online-only "LOC 100% en ligne" offices), so follow the store
    # finder's own department search instead.
    start_urls = ["https://fr.foncia.com/agence-immobiliere/toutes-les-agences-par-departement"]
    wanted_types = ["RealEstateAgent"]
    drop_attributes = {"facebook", "twitter"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for slug in response.xpath("//a/@href").re(r"/agence-immobiliere/agences-immobilieres/([^/?#]+)$"):
            yield JsonRequest(
                url="https://fnc-api.prod.fonciatech.net/agences/agences/search",
                data={"page": 1, "size": 150, "filters": {"activites": [], "slug": slug}},
                callback=self.parse_agencies,
            )

    def parse_agencies(self, response: Response, **kwargs: Any) -> Any:
        for agency in response.json()["agences"]:
            yield response.follow("https://fr.foncia.com" + agency["canonicalUrl"], callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for rule in ld_data.get("openingHoursSpecification") or []:
            days = rule.get("dayOfWeek")
            if isinstance(days, str):
                days = [days]
            rule["dayOfWeek"] = [sanitise_day(day, DAYS_FR) for day in days or []]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("-", 1)[1]
        if re.match(r"foncia\b", item["name"], flags=re.IGNORECASE):
            item["branch"] = item.pop("name")[len("foncia") :].strip(" -")
        item["website"] = response.url
        if "agence-default-photo" in (item.get("image") or ""):
            item.pop("image")
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
