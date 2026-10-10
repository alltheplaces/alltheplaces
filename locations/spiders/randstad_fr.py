import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RandstadFRSpider(SitemapSpider, StructuredDataSpider):
    name = "randstad_fr"
    item_attributes = {"brand": "Randstad", "brand_wikidata": "Q267840", "name": "Randstad"}
    allowed_domains = ["www.randstad.fr"]
    sitemap_urls = ["https://www.randstad.fr/sitemap-offices.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["EmploymentAgency"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        item.pop("image", "")
        item["branch"] = item.pop("name", "")

        oh = OpeningHours()
        for row in response.css("ul.time-table > li.time-table__item"):
            day = DAYS_FR.get(row.css(".time-table__day::text").get("").strip().rstrip(":").capitalize())
            if not day:
                continue
            for time_range in row.css(".time-table__time::text").getall():
                if m := re.match(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", time_range.strip()):
                    oh.add_range(day, m.group(1), m.group(2))
        item["opening_hours"] = oh

        yield item
