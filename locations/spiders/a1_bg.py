import scrapy

from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.items import Feature


class A1BGSpider(scrapy.Spider):
    name = "a1_bg"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q1941592", "country": "BG"}
    allowed_domains = ["www.a1.bg"]
    start_urls = ["https://www.a1.bg/1/mm/shops/mc/index/ma/index/mo/1?ajaxaction=getShopsWithWorkTime"]

    def parse(self, response):
        for store in response.json()["response"]:
            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store["name"]
            item["addr_full"] = store["address"].strip()
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["phone"] = store["phone"]

            item["opening_hours"] = OpeningHours()
            for day in store["worktime"]:
                item["opening_hours"].add_range(
                    sanitise_day(day["weekday"], DAYS_BG),
                    day["hour_from"],
                    day["hour_to"],
                    "%H:%M:%S",
                )

            yield item
