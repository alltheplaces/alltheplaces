from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class SleepNumberUSSpider(Spider):
    name = "sleep_number_us"
    item_attributes = {"brand_wikidata": "Q7447640", "brand": "Sleep Number", "extras": Categories.SHOP_BED.value}
    start_urls = [
        "https://www.sleepnumber.com/api/storefront/store-locations?lat=42.8473561&lng=-106.26166833&limit=10000&radius=25000"
    ]

    def parse(self, response):
        for store in response.json()["entities"]:
            item = DictParser.parse(store)
            item["ref"] = store["cid"]
            item["website"] = store["c_storePagesURLURL"]

            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in store.get("hours", {}).items():
                if not isinstance(day_hours, dict) or day_hours.get("isClosed") or day_name.title() not in DAYS_FULL:
                    continue
                for time_period in day_hours["openIntervals"]:
                    item["opening_hours"].add_range(day_name.title(), time_period["start"], time_period["end"])

            yield item
