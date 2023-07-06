import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_SI, OpeningHours, sanitise_day


class HoferSISpider(scrapy.Spider):  # Aldi Sud
    name = "hofer_si"
    item_attributes = {"brand": "Hofer", "brand_wikidata": "Q15815751"}
    start_urls = [
        "https://www.hofer.si/si/sl/.get-stores-in-radius.json?latitude=46.23974949999999&longitude=15.2677063&radius=2500000"
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            if store["storeType"] == "N":
                continue
            if item["country"] != "SI":
                continue

            item["website"] = store.get("url")

            oh = OpeningHours()
            for rule in store["openUntilSorted"]["openingHours"]:
                day = sanitise_day(rule["day"].replace(".", ""), DAYS_SI)
                if not rule.get("closed", False):
                    oh.add_range(
                        day,
                        rule["openFormatted"],
                        rule["closeFormatted"],
                        time_format="%H.%M",
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
