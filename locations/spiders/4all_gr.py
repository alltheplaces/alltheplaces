import html
import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# ISO weekday numbers: 1=Monday … 7=Sunday
OH_DAYS = {"1": "Mo", "2": "Tu", "3": "We", "4": "Th", "5": "Fr", "6": "Sa", "7": "Su"}


class FourAllGRSpider(Spider):
    name = "4all_gr"
    item_attributes = {"brand": "4all", "brand_wikidata": "Q130279387", "country": "GR"}
    start_urls = ["https://4allstores.gr/wp-admin/admin-ajax.php?action=filter_stores&storesArea="]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any):
        data = response.json()
        for i, store in enumerate(data.get("data", [])):
            lat = store.get("latitude")
            lon = store.get("longitude")
            if not lat or not lon:
                continue

            item = Feature()
            item["ref"] = str(i + 1)
            item["lat"] = float(lat)
            item["lon"] = float(lon)

            # Title is "STREET_ADDRESS, CITY" or "STREET – CITY" (Greek em dash variant)
            title = html.unescape(store.get("title", "")).strip()
            if ", " in title:
                parts = title.rsplit(", ", 1)
                item["street_address"] = parts[0].strip().title()
                item["city"] = parts[1].strip().title()
            elif " – " in title or " \u2013 " in title:
                parts = re.split(r"\s+[\u2013-]\s+", title, maxsplit=1)
                if len(parts) == 2:
                    item["street_address"] = parts[0].strip().title()
                    item["city"] = parts[1].strip().title()
                else:
                    item["street_address"] = title.title()
            else:
                item["street_address"] = title.title()

            # Opening hours: keys "1"-"7" = Mon-Sun, values "HH:MM - HH:MM" or ""
            oh_data = store.get("opening_hours", {})
            if any(v for v in oh_data.values()):
                oh = OpeningHours()
                for day_key, time_str in oh_data.items():
                    day = OH_DAYS.get(day_key)
                    if not day:
                        continue
                    if not time_str:
                        oh.set_closed(day)
                        continue
                    m = re.match(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", time_str.strip())
                    if m:
                        oh.add_range(day, m.group(1), m.group(2))
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
