from typing import Any, AsyncIterator

from chompjs import parse_js_object
from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class MaxmaraSpider(Spider):
    name = "maxmara"
    item_attributes = {"brand": "Max Mara", "brand_wikidata": "Q1151774"}
    gc = GeonamesCache()
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country_code in self.gc.get_countries().keys():
            yield JsonRequest(
                url=f"https://us.maxmara.com/store-locator?listJson=true&withoutRadius=false&country={country_code}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = parse_js_object(response.text).get("features", [])
        for store in stores:
            if not store.get("storeHidden"):
                store_info = store["properties"]
                item = DictParser.parse(store_info)
                item["ref"] = item.pop("name")
                item["branch"] = (
                    store_info["displayName"].replace("MaxMara ", "").replace("Max Mara ", "").lstrip("(").rstrip(")")
                )
                item["phone"] = store_info["phone1"]
                item["addr_full"] = store_info["formattedAddress"]

                oh = OpeningHours()
                for day, hours in store_info.get("openingHours").items():
                    for time_period in hours:
                        open_at, close_at = time_period.replace(".", ":").split(" - ")
                        oh.add_range(day=DAYS_EN[day], open_time=open_at, close_time=close_at, time_format="%I:%M %p")
                item["opening_hours"] = oh

                apply_category(Categories.SHOP_CLOTHES, item)
                apply_clothes([Clothes.WOMEN], item)

                yield item
