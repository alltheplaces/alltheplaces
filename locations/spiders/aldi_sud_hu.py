from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_HU, OpeningHours, sanitise_day


class AldiSudHUSpider(Spider):
    name = "aldi_sud_hu"
    item_attributes = {"brand_wikidata": "Q41171672"}
    start_urls = [
        "https://www.aldi.hu/hu/hu/.get-stores-in-radius.json?latitude=47.162494&longitude=19.503304&radius=2500000"
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            if store["storeType"] == "N":
                continue
            if item["country"] != "HU":
                continue
            item["name"] = None  # ref

            item["website"] = store.get("url")

            oh = OpeningHours()
            for rule in store["openUntilSorted"]["openingHours"]:
                day = sanitise_day(rule["day"], DAYS_HU)
                if not rule.get("closed", False):
                    oh.add_range(day, rule["openFormatted"], rule["closeFormatted"])
            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
