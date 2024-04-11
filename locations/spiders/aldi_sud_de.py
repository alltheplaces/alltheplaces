import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class AldiSudDESpider(scrapy.Spider):
    name = "aldi_sud_de"
    item_attributes = {"name": "ALDI Süd", "brand": "ALDI Süd", "brand_wikidata": "Q41171672"}
    start_urls = [
        "https://www.aldi-sued.de/de/de/.get-stores-in-radius.json?latitude=44.721772724757756&longitude=18.98679905523246&radius=2500000"
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["name"] = None
            if store["storeType"] == "N":
                continue  # AldiNordDESpider
            if item["country"] != "DE":
                continue

            item["website"] = store.get("url")

            oh = OpeningHours()
            for rule in store["openUntilSorted"]["openingHours"]:
                day = sanitise_day(rule["day"], DAYS_DE)
                if not rule.get("closed", False):
                    oh.add_range(day, rule["openFormatted"], rule["closeFormatted"])
            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
