import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class SephoraGBSpider(Spider):
    name = "sephora_gb"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    start_urls = ["https://www.sephora.co.uk/stores/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_json in response.xpath("//@data-feelunique-store-info").getall():
            store = json.loads(store_json)
            item = DictParser.parse(store)
            item["ref"] = store.get("code")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")

            item["opening_hours"] = OpeningHours()
            for entry in store.get("openHours", []):
                day_index = entry.get("dow")
                if day_index is None:
                    continue
                day_index -= 1
                if 0 <= day_index < 7:
                    day = DAYS_FROM_SUNDAY[day_index]
                    try:
                        item["opening_hours"].add_range(day, entry["start"][:5], entry["end"][:5])
                    except (KeyError, ValueError):
                        continue

            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
