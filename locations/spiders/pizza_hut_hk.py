import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class PizzaHutHKSpider(scrapy.Spider):
    name = "pizza_hut_hk"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    start_urls = [
        "https://jrgapp.aigens.com/api/v1/store/store.json?brandId=599961624702976",
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["addr_full"] = store.get("location").get("line")
            item["opening_hours"] = OpeningHours()
            for day_time in store.get("openings").get("weekdays"):
                day = day_time.get("weekday")
                start_time = day_time.get("startTime")
                close_time = day_time.get("endTime")
                item["opening_hours"].add_range(day=DAYS_FULL[day], open_time=start_time, close_time=close_time)
            yield item
