import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_CH, OpeningHours, sanitise_day


class AldiSudCHSpider(scrapy.Spider):
    name = "aldi_sud_ch"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672"}
    start_urls = [
        "https://www.aldi-suisse.ch/ch/de/.get-stores-in-radius.json?latitude=47.61956488197022&longitude=8.110630887500013&radius=2500000"
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            if store["storeType"] == "N":
                continue
            if item["country"] != "CH":
                continue

            item["website"] = store.get("url")

            oh = OpeningHours()
            for rule in store["openUntilSorted"]["openingHours"]:
                day = sanitise_day(rule["day"], DAYS_CH)
                if not rule.get("closed", False):
                    oh.add_range(day, rule["openFormatted"], rule["closeFormatted"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
