from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


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

            # This structure appears in multiple other spiders, should refactor.
            # carhartt_wip, nissan_europe, stbant, primark.
            oh = OpeningHours()
            day_data = store.get("hours") or {}
            day_dict = dict(day_data)
            for day, value in day_dict.items():
                value = dict(value)
                if value == {} or value.get("isClosed"):
                    continue
                for interval in value.get("openIntervals"):
                    oh.add_range(
                        day=day.title()[:2],
                        open_time=interval.get("start"),
                        close_time=interval.get("end"),
                        time_format="%H:%M",
                    )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
