import json
import urllib.parse
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

COUNTRIES = {
    "AE": {"lat": "24.4460177", "lng": "54.6517068"},
    "SA": {"lat": "24.56325", "lng": "46.7914587"},
    "KW": {"lat": "29.364853", "lng": "47.979266"},
    "BH": {"lat": "26.2235305", "lng": "50.5875935"},
    "QA": {"lat": "25.2854473", "lng": "51.5310397"},
    "OM": {"lat": "23.5880", "lng": "58.3829"},
}


class SephoraMESpider(Spider):
    name = "sephora_me"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        for cc, coords in COUNTRIES.items():
            input_data = {
                "json": {
                    "locale": f"en-{cc}",
                    "getServices": True,
                    "latitude": coords["lat"],
                    "longitude": coords["lng"],
                    "limit": "200",
                    "maxDistance": "5000",
                }
            }
            encoded = urllib.parse.quote(json.dumps(input_data))
            url = f"https://www.sephora.me/api/trpc/store.searchStores?input={encoded}"
            yield Request(url, cb_kwargs={"country": cc})

    def parse(self, response: Response, country: str, **kwargs: Any) -> Any:
        data = response.json()
        stores = data["result"]["data"]["json"]["data"]
        for store in stores:
            item = DictParser.parse(store)
            item["ref"] = store.get("id")
            item["branch"] = item.pop("name", "").title()
            item["street_address"] = store.get("address1")
            item["country"] = country

            self._parse_hours(item, store.get("c_weeklyOpeningHours", {}), store.get("c_storeInfo", {}))

            apply_category(Categories.SHOP_COSMETICS, item)
            yield item

    @staticmethod
    def _parse_hours(item: Feature, weekly_hours: dict, store_info: dict) -> None:
        oh = OpeningHours()
        # Try c_weeklyOpeningHours Time strings first (24h format)
        for day_index, entry in weekly_hours.items():
            try:
                idx = int(day_index)
                if 0 <= idx < 7:
                    day = DAYS_FROM_SUNDAY[idx]
                    time_str = entry.get("Time", "")
                    for part in time_str.split(","):
                        part = part.strip()
                        if " - " in part:
                            open_time, close_time = part.split(" - ", 1)
                            oh.add_range(day, open_time.strip(), close_time.strip())
            except (ValueError, TypeError):
                continue
        if oh.as_opening_hours():
            item["opening_hours"] = oh
            return
        # Fallback to c_storeInfo.schedule (12h format with English day names)
        for entry in store_info.get("schedule", []):
            try:
                oh.add_ranges_from_string(f"{entry['Day']} {entry['Time']}", days=DAYS_EN)
            except Exception:
                continue
        item["opening_hours"] = oh
