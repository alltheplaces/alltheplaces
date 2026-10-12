import re
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ManpowerPartooSpider(SitemapSpider, StructuredDataSpider):
    """
    Manpower's branch locators in BE, CH, DE, ES, FR, GB and LU are separate sites built on the same Partoo store
    locator. This class contains their common spider code.
    """

    item_attributes = {"brand": "Manpower", "brand_wikidata": "Q1472539"}
    wanted_types = ["EmploymentAgency"]
    search_for_facebook = False
    search_for_twitter = False

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        entries = list(entries)
        urls = [entry["loc"] for entry in entries]
        for entry in entries:
            # Region and city pages are a prefix of another URL, branch pages never are.
            if not any(url.startswith(entry["loc"].rstrip("/") + "/") for url in urls):
                yield entry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        name = item.pop("name", None) or ""
        # The locators also list other ManpowerGroup brands (AviationPower, Brook Street).
        if "Manpower" not in name:
            return
        # "Manpower UK Leeds" -> "Leeds", "Manpower AG - Bern" -> "Bern", "Cabinet Manpower Blois" -> "Cabinet Blois"
        item["branch"] = re.sub(r"\bManpower(?: UK| AG)?\b[ -]*", "", name, count=1) or None
        # The "@id" ends in the locator's own store number; a branch listed under two URLs shares it.
        item["ref"] = item["ref"].rsplit("#store-", 1)[-1]
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        yield item
