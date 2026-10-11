from typing import Iterable

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
    ]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["EmploymentAgency"]
    search_for_facebook = False
    search_for_twitter = False
    search_for_instagram = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Manpower ").removeprefix("UK ")
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        yield item
