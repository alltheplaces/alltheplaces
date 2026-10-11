import re
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ManpowerSpider(SitemapSpider, StructuredDataSpider):
    name = "manpower"
    item_attributes = {"brand": "Manpower", "brand_wikidata": "Q1472539"}
    sitemap_urls = [
        "https://www.standorte.manpower.de/sitemap.xml",
        "https://oficinas.manpower.es/sitemap.xml",
        "https://locations.manpower.co.uk/sitemap.xml",
        "https://interim-branches.manpower.be/sitemap.xml",
        "https://standorte.manpower.ch/de/sitemap.xml",
    ]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["EmploymentAgency"]
    search_for_facebook = False
    search_for_twitter = False
    search_for_instagram = False

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            # The Swiss sitemap omits the language prefix, without which its pages are 404.
            entry["loc"] = entry["loc"].replace("manpower.ch/", "manpower.ch/de/")
            yield entry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # The locators also list other ManpowerGroup brands (AviationPower, Brook Street).
        if not item["name"].startswith("Manpower"):
            return
        item["branch"] = re.sub(r"^Manpower(?: UK| AG)?\b[ -]*", "", item.pop("name")) or None
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        yield item
