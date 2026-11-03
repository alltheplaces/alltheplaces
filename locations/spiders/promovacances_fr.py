import re
from typing import Any, Iterable

from scrapy.http import Response, TextResponse

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class PromovacancesFRSpider(StructuredDataSpider):
    name = "promovacances_fr"
    item_attributes = {"brand": "Promovacances", "brand_wikidata": "Q3407444"}
    allowed_domains = ["www.promovacances.com"]
    start_urls = ["https://www.promovacances.com/agences-de-voyages/"]
    wanted_types = ["TravelAgency"]
    drop_attributes = {"twitter"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ld_item in LinkedDataParser.iter_linked_data(response):
            if ld_item.get("@type") != "ItemList":
                continue
            for agency in ld_item["itemListElement"]:
                yield response.follow(agency["url"].rstrip("/") + "/", callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # Days are in French, which the default parser does not read
        ld_data["frenchOpeningHours"] = ld_data.pop("openingHoursSpecification", [])

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^((Promovacances?|Agence)\s*-?\s*)+", "", item.pop("name"))
        item["ref"] = response.url

        oh = OpeningHours()
        for rule in ld_data["frenchOpeningHours"]:
            for day in rule["dayOfWeek"]:
                oh.add_range(DAYS_FR[day.title()], rule["opens"], rule["closes"])
        item["opening_hours"] = oh

        yield item
