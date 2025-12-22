from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class SleepNumberUSSpider(Spider):
    name = "sleep_number_us"
    item_attributes = {"brand": "Sleep Number", "brand_wikidata": "Q7447640"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "DOWNLOAD_TIMEOUT": 90,
        "CONCURRENT_REQUESTS": 1,
        "RETRY_TIMES": 5,
        "DOWNLOAD_DELAY": 3,
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 458):
            yield JsonRequest(
                url="https://www.sleepnumber.com/api/storefront/store-locations?lat={}&lng={}&limit=100&radius=300".format(
                    lat, lon
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["entities"]:
            item = DictParser.parse(store)
            item["ref"] = item["website"] = store["c_storePagesURLURL"]
            item["extras"]["ref:google:place_id"] = store.get("googlePlaceId")

            try:
                item["opening_hours"] = self.parse_opening_hours(store.get("hours", {}))
            except:
                self.logger.error("Error parsing opening hours")

            apply_category(Categories.SHOP_BED, item)

            yield item

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day_name, day_hours in hours.items():
            if "holiday" in day_name:
                continue
            if not day_hours:
                continue
            if day_hours.get("isClosed"):
                oh.set_closed(day_name)
            else:
                for time_period in day_hours["openIntervals"]:
                    oh.add_range(day_name, time_period["start"], time_period["end"])
        return oh
