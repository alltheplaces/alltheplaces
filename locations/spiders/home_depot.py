import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class HomeDepotSpider(Spider):
    name = "home_depot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.storelocators.com"]
    start_urls = ["https://www.storelocators.com/store-lists/assets/_data/home_depot.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = self.extract_stores(response.text)
        for store in stores:
            if store.get("country") != "US":
                continue

            item = Feature()
            state = store.get("state") or self.state_for_store(store)
            item["ref"] = self.make_ref(store, state)
            item["name"] = "The Home Depot"
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["street_address"] = store.get("address")
            item["city"] = store.get("city")
            item["state"] = state
            item["postcode"] = store.get("zip")
            item["country"] = "US"
            item["phone"] = store.get("phone")
            item["website"] = "https://www.homedepot.com/l/storeDirectory"

            if store.get("hours"):
                item["opening_hours"] = self.parse_hours(store["hours"])

            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item

    @staticmethod
    def extract_stores(script: str) -> list[dict]:
        match = re.search(r"var\s+ALL_STORES\s*=\s*(\[.*?\]);?\s*$", script, flags=re.S)
        if not match:
            raise ValueError("Could not find ALL_STORES in StoreLocators Home Depot data file")
        return json.loads(match.group(1))

    @staticmethod
    def parse_hours(hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day_number, day_name in enumerate(DAYS_FROM_SUNDAY):
            day_hours = hours.get(str(day_number))
            if not day_hours or not day_hours.get("open") or not day_hours.get("close"):
                continue
            opening_hours.add_range(day_name, day_hours["open"], day_hours["close"], "%H:%M:%S")
        return opening_hours

    @staticmethod
    def state_for_store(store: dict) -> str | None:
        if str(store.get("zip", "")).startswith("008"):
            return "VI"
        return None

    @staticmethod
    def make_ref(store: dict, state: str | None) -> str:
        ref_parts = [store.get("address"), store.get("city"), state, store.get("zip")]
        raw_ref = "-".join(str(part or "") for part in ref_parts).lower().replace("&", "and")
        return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", raw_ref))[:180]
