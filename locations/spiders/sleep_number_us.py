from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SleepNumberUSSpider(Spider):
    name = "sleep_number_us"
    item_attributes = {"brand": "Sleep Number", "brand_wikidata": "Q7447640"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def start_requests(self):
        for lat, lon in [
            (21.30694, -157.85833),
            (26.12231, -80.14338),
            (30.44332, -91.18747),
            (39.95238, -75.16362),
            (44.97997, -93.26384),
        ]:
            yield JsonRequest(
                url="https://www.sleepnumber.com/api/storefront/store-locations?lat={}&lng={}&limit=190&radius=25000".format(
                    lat, lon
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["entities"]:
            item = DictParser.parse(store)
            item["ref"] = store["cid"]
            item["website"] = store["c_storePagesURLURL"]
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
            if not day_hours:
                continue
            if day_hours.get("isClosed"):
                oh.set_closed(day_name)
            else:
                for time_period in day_hours["openIntervals"]:
                    oh.add_range(day_name, time_period["start"], time_period["end"])
        return oh
