# -*- coding: utf-8 -*-
import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TechnomarketBGSpider(scrapy.Spider):
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
            item["street_address"] = store["address"].strip()
            item["lat"] = store["latLng"]["lat"]
            item["lon"] = store["latLng"]["lng"]
            item["phone"] = store["tel"]
            item["email"] = store["email"]
            item["website"] = (
                "https://www.technomarket.bg/magazini/" + store["url"]["city"] + "/" + store["url"]["store"]
            )

            oh = OpeningHours()
            for day in DAYS[0:5]:
                if store["wh"][0] == "Почивен ден":
                    # "day off" = closed
                    continue

                from_str, to_str = store["wh"][0].split(" до ")
                oh.add_range(day, from_str.strip(), to_str.strip(), "%H:%M")

            for day in DAYS[5:6]:
                if store["wh"][1] == "Почивен ден":
                    # "day off" = closed
                    continue

                from_str, to_str = store["wh"][1].split(" до ")
                oh.add_range(day, from_str.strip(), to_str.strip(), "%H:%M")

            for day in DAYS[6:7]:
                if store["wh"][2] == "Почивен ден":
                    # "day off" = closed
                    continue

                from_str, to_str = store["wh"][2].split(" до ")
                oh.add_range(day, from_str.strip(), to_str.strip(), "%H:%M")

            item["opening_hours"] = oh.as_opening_hours()

            yield item
