from typing import Any, Iterable

import chompjs
import scrapy
from geonamescache import GeonamesCache
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MaxmaraSpider(scrapy.Spider):
    name = "maxmara"
    item_attributes = {"brand": "Max Mara", "brand_wikidata": "Q1151774"}
    gc = GeonamesCache()
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self) -> Iterable[JsonRequest]:
        for country_code in self.gc.get_countries().keys():
            yield JsonRequest(
                url=f"https://us.maxmara.com/store-locator?listJson=true&withoutRadius=false&country={country_code}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = chompjs.parse_js_object(response.text).get("features", [])
        for store in stores:
            if not store.get("storeHidden"):
                store_info = store["properties"]
                item = DictParser.parse(store_info)
                item["ref"] = store_info["name"]
                item["name"] = store_info["displayName"]
                item["phone"] = store_info["phone1"]
                item["addr_full"] = store_info["formattedAddress"]

                oh = OpeningHours()
                for day, hours in store_info.get("openingHours").items():
                    for chunk in hours:
                        open_at, close_at = chunk.replace(".", ":").split(" - ")
                        oh.add_range(day=DAYS_EN[day], open_time=open_at, close_time=close_at, time_format="%H:%M")
                item["opening_hours"] = oh

                apply_category(Categories.SHOP_CLOTHES, item)
                apply_clothes([Clothes.WOMEN], item)

                yield item
