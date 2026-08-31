import html
import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class WoodcraftUSSpider(Spider):
    name = "woodcraft_us"
    item_attributes = {"brand": "Woodcraft", "brand_wikidata": "Q22026341"}
    start_urls = ["https://www.woodcraft.com/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Stores are embedded as a JSON array in a JSON.parse() call within a <script> tag
        for script_text in response.xpath(
            '//script[contains(text(), "const stores = JSON.parse") and contains(text(), "coordinate_latitude")]/text()'
        ).getall():
            m = re.search(r"const stores = JSON\.parse\(`\s*(\[)", script_text)
            if not m:
                continue
            raw = script_text[m.start(1) :]
            depth = 0
            end = 0
            for i, ch in enumerate(raw):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            stores = json.loads(html.unescape(raw[:end]))
            for store in stores:
                yield from self.parse_store(store)
            return

    def parse_store(self, store: dict) -> Any:
        item = Feature()
        item["ref"] = store.get("_id") or store.get("slug")
        item["branch"] = store["name"].removeprefix("Woodcraft ").removeprefix("of ").strip()
        item["lat"] = store.get("coordinate_latitude")
        item["lon"] = store.get("coordinate_longitude")
        item["street_address"] = store.get("street")
        item["city"] = store.get("city")
        item["state"] = store.get("state")
        item["postcode"] = store.get("zip")
        item["country"] = "US"
        item["phone"] = store.get("phone_number")
        item["email"] = store.get("email")
        item["website"] = "https://www.woodcraft.com/pages/store/{}".format(store.get("slug", ""))

        hours_data = store.get("hours", {})
        if hours_data:
            oh = OpeningHours()
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                time_str = hours_data.get(day, "")
                if time_str:
                    oh.add_ranges_from_string("{} {}".format(day.title(), time_str))
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_CRAFT, item)
        yield item
