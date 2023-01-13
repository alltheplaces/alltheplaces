import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {0: "Mo-Fr", 1: "Sa", 2: "Su"}


class TechnomarketSpider(scrapy.Spider):
    name = "technomarket_bg"
    item_attributes = {"brand": "Техномаркет", "brand_wikidata": "Q7692633", "country": "BG"}
    allowed_domains = ["www.technomarket.bg"]
    start_urls = ["https://www.technomarket.bg/api/frontend/stores"]

    def parse(self, response):
        data = response.json()

        for store in data:
            item = Feature()
            item["ref"] = store["code"]
            item["name"] = store["name"]
            item["addr_full"] = store["address"].strip()
            item["lat"] = store["latLng"]["lat"]
            item["lon"] = store["latLng"]["lng"]
            item["phone"] = store["tel"]
            item["email"] = store["email"]
            item["website"] = "https://www.technomarket.bg/" + store["url"]["city"] + "/" + store["url"]["store"]

            oh = OpeningHours()
            for index, day in enumerate(store["wh"]):
                oh.add_range(
                    DAY_MAPPING[index],
                    day.split(" до ")[0],
                    day.split(" до ")[1],
                    "%H:%M",
                )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
