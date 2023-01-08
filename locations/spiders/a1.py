import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Понеделник": "Mo",
    "Вторник": "Tu",
    "Сряда": "We",
    "Четвъртък": "Th",
    "Петък": "Fr",
    "Събота": "Sa",
    "Неделя": "Su",
}


class A1Spider(scrapy.Spider):
    name = "a1"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q1941592", "country": "BG"}
    allowed_domains = ["www.a1.bg"]
    start_urls = ["https://www.a1.bg/1/mm/shops/mc/index/ma/index/mo/1?ajaxaction=getShopsWithWorkTime"]

    def parse(self, response):
        data = response.json()

        for store in data["response"]:
            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store["name"]
            item["addr_full"] = store["address"].strip()
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]

            if store.get("phone"):
                item["phone"] = "+" + store["phone"]

            oh = OpeningHours()
            for day in store["worktime"]:
                oh.add_range(
                    DAY_MAPPING[day["weekday"]],
                    day["hour_from"],
                    day["hour_to"],
                    "%H:%M:%S",
                )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
