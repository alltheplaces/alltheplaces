from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class HoferATSpider(Spider):  # Aldi Sud
    name = "hofer_at"
    item_attributes = {"brand": "Hofer", "brand_wikidata": "Q15815751"}
    start_urls = [
        "https://www.hofer.at/at/de/.get-stores-in-radius.json?latitude=47.516231&longitude=14.550072&radius=2500000"
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            if store["storeType"] == "N":
                continue
            if item["country"] != "AT":
                continue

            item["website"] = store.get("url")

            oh = OpeningHours()
            for rule in store["openUntilSorted"]["openingHours"]:
                day = sanitise_day(rule["day"], DAYS_DE)
                if not rule.get("closed", False):
                    oh.add_range(day, rule["openFormatted"], rule["closeFormatted"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
