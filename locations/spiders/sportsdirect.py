import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SportsDirectSpider(scrapy.Spider):
    name = "sportsdirect"

    custom_settings = {"ROBOTSTXT_OBEY": False}
    available_countries = [
        "MY",
        "FR",
        "AT",
        "CY",
        "DE",
        "EE",
        "KW",
        "IE",
        "LU",
        "PL",
        "SI",
        "CZ",
        "GB",
        "AE",
        "IS",
        "HU",
        "ES",
        "LV",
        "SK",
        "BE",
        "LT",
        "PT",
        "SA",
        "RW",
    ]
    brand_mapping = {
        "Sports Direct": {"brand": "Sports Direct", "brand_wikidata": "Q7579661"},
        "Lillywhites": {"brand": "Lillywhites", "brand_wikidata": "Q6548397"},
        "Field \u0026 Trek": {"brand": "Field & Trek"},
    }

    def start_requests(self):
        for country in self.available_countries:
            yield scrapy.Request(
                f"https://be.sportsdirect.com/stores/search?countryName=Verenigd%20Koninkrijk&countryCode={country}&lat=0&long=0&sd=10",
            )

    def parse(self, response, **kwargs):
        pattern = r"var\s+stores\s*=\s*(\[.*?\]);\s*var"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            oh = OpeningHours()
            for day in store["openingTimes"]:
                oh.add_range(
                    day=DAYS[day["dayOfWeek"]],
                    open_time=day["openingTime"],
                    close_time=day["closingTime"],
                    time_format="%H:%M",
                )
            item = DictParser.parse(store)
            item["ref"] = store["code"]
            item["brand"] = self.brand_mapping[store["storeType"]]["brand"]
            item["brand_wikidata"] = self.brand_mapping[store["storeType"]].get("brand_wikidata")
            item["opening_hours"] = oh
            yield item
