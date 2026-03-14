import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TargetUSSpider(SitemapSpider):
    name = "target_us"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q1046951"}
    allowed_domains = ["target.com"]
    sitemap_urls = ["https://www.target.com/sitemap_stores-index.xml.gz"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUESTS": 1}
    api_key = "8df66ea1e1fc070a6ea99e942431c9cd67a80f02"

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            if slug := re.search(r"/sl/[^/]+/(\d+)$", entry["loc"]):
                entry["loc"] = (
                    f"https://redsky.target.com/redsky_aggregations/v1/web/store_locations_v1?key={self.api_key}&store_id={slug.group(1)}"
                )
            yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if store := response.json().get("data", {}).get("store"):
            store.update(store.pop("mailing_address"))
            store.update(store.pop("geographic_specifications"))
            item = DictParser.parse(store)
            item["name"] = None
            item["branch"] = store.get("location_name")
            item["website"] = (
                f'https://www.target.com/sl/{item["branch"].lower().replace(" ", "-")}/{store["store_id"]}'
            )
            for contact_info in store.get("contact_information", []):
                if contact_info.get("telephone_type") == "VOICE":
                    item["phone"] = contact_info.get("telephone_number")
                elif contact_info.get("telephone_type") == "FAX":
                    item["extras"]["fax"] = contact_info.get("telephone_number")

            opening_hours_info = store.get("rolling_operating_hours", {}).get("main_hours", {}).get("days") or []
            item["opening_hours"] = self.parse_opening_hours(opening_hours_info)

            if store.get("physical_specifications", {}).get("format") == "SuperTarget":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules[:7]:
            day = rule.get("day_name")
            if rule.get("is_open") is False:
                oh.set_closed(day)
                continue
            for shift in rule.get("hours", []):
                oh.add_range(day, shift["begin_time"], shift["end_time"], "%H:%M:%S")
        return oh
