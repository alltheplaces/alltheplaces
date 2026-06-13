import json
from html import unescape
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

DAY_MAP = {day.upper(): DAYS_FULL[i] for i, day in enumerate(DAYS_FULL)}


class BioburgerFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bioburger_fr"
    item_attributes = {"brand": "Bioburger", "brand_wikidata": "Q139679401"}
    sitemap_urls = ["https://restaurants.bioburger.fr/robots.txt"]
    sitemap_rules = [(r"/restaurant-burger-bio/([^/]+)/$", "parse")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Bioburger ")

        # addr:state is incorrectly set to the country code by structured data
        item.pop("state", None)

        # Drop placeholder images
        if "placeholder" in (item.get("image") or ""):
            item.pop("image", None)

        # Parse opening hours from the data-information attribute
        raw = response.css("[data-information]").attrib.get("data-information")
        if raw:
            info = json.loads(unescape(raw))
            seen_days = set()
            oh = OpeningHours()
            for entry in info.get("hours", []):
                day_key = entry["day"]
                if day_key in seen_days:
                    continue
                seen_days.add(day_key)
                for period in entry.get("periods", []):
                    if period.get("isClosed"):
                        continue
                    oh.add_range(DAY_MAP[day_key], period["openTime"], period["closeTime"])
            item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.FAST_FOOD, item)
        yield item
