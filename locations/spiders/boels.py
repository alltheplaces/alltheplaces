from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BoelsSpider(SitemapSpider, StructuredDataSpider):
    name = "boels"
    item_attributes = {"brand": "Boels", "brand_wikidata": "Q19901961"}
    sitemap_urls = ["https://www.boels.com/robots.txt"]
    sitemap_rules = [(r"https://www.boels.com/en-\w\w/branches/[\w+]", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Boels ").replace("; ", " - ")
        item["state"] = None

        try:
            if ld_data.get("openingHoursSpecification"):
                item["opening_hours"] = self.parse_opening_hours(ld_data["openingHoursSpecification"])
        except Exception:
            pass

        apply_category(Categories.SHOP_TOOL_HIRE, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            rule["dayOfWeek"] = rule["dayOfWeek"].removeprefix("https://www.schema.org/")
            if rule["opens"] == rule["closes"] == "00:00":
                oh.set_closed(rule["dayOfWeek"])
            else:
                if " &amp; " in rule["opens"]:
                    start_1, start_2 = rule["opens"].split(" &amp; ")
                    end_1, end_2 = rule["closes"].split(" &amp; ")
                    oh.add_range(rule["dayOfWeek"], start_1, end_1)
                    oh.add_range(rule["dayOfWeek"], start_2, end_2)
                else:
                    oh.add_range(rule["dayOfWeek"], rule["opens"], rule["closes"])
        return oh
