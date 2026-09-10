import json
from typing import Iterable

from scrapy.http import Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SamsicEmploiFRSpider(CrawlSpider, StructuredDataSpider):
    name = "samsic_emploi_fr"
    item_attributes = {"brand": "Samsic Emploi", "brand_wikidata": "Q136431282"}
    allowed_domains = ["www.samsic-emploi.fr"]
    start_urls = ["https://www.samsic-emploi.fr/nos-agences/tous-nos-etablissements"]
    rules = [Rule(LinkExtractor(allow=r"samsic-emploi.fr/nos-agences/[^/]+/[^/]+/[^/]+$"), callback="parse_sd")]
    wanted_types = ["EmploymentAgency"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        raw = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "EmploymentAgency")]/text()'
        ).get()
        if raw:
            yield from json.loads(raw)["@graph"][0]["itemListElement"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        item.pop("facebook", "")
        item.pop("image", "")
        item["branch"] = item.pop("name", "").removeprefix("Samsic Emploi ")
        yield item
