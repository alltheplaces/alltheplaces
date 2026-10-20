import json
import re
from typing import Any
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class PizzaHutUSSpider(SitemapSpider, StructuredDataSpider):
    name = "pizza_hut_us"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615", "extras": Categories.RESTAURANT.value}
    sitemap_urls = ["https://locations.pizzahut.com/robots.txt"]
    sitemap_rules = [
        (
            r"^https://locations\.pizzahut\.com/\w\w/[^/]+/(?!pizzeria|food-places|takeout|pizza-deals|pizza-delivery|wings|lunch-specials|pizza-near-me|pizza-and-wings-near-me)[^/]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["FastFoodRestaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        document = self.extract_document(response)
        if "reopenDate" in document.get("hours", {}):
            return
        days = {day: document.get("hours", {}).get(day.lower()) for day in DAYS_FULL}
        days = {day: day_hours for day, day_hours in days.items() if day_hours}
        if "coming soon" in document.get("c_deliveryHoursAdditionalInfo", "").lower() and not any(
            day_hours.get("openIntervals") for day_hours in days.values()
        ):
            return
        label = response.xpath('//h1[@class="H1"]/text()').get()
        if not label:
            set_closed(item)
        if label == "Pizza Hut Express":
            item["name"] = "Pizza Hut Express"
            apply_category(Categories.FAST_FOOD, item)
        else:
            apply_category(Categories.RESTAURANT, item)

        if days:
            item["opening_hours"] = self.parse_hours(days)

        yield item

    @staticmethod
    def extract_document(response: Response) -> dict[str, Any]:
        blob = re.search(r'decodeURIComponent\("([^"]+)"\)', response.xpath('//script[@type="module"]/text()').get(""))
        return json.loads(unquote(blob.group(1))).get("document", {}) if blob else {}

    @staticmethod
    def parse_hours(days: dict[str, Any]) -> OpeningHours:
        oh = OpeningHours()
        for day, day_hours in days.items():
            if day_hours.get("isClosed"):
                oh.set_closed(day)
                continue
            for interval in day_hours.get("openIntervals", []):
                oh.add_range(day, interval["start"], interval["end"])
        return oh
