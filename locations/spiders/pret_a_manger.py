import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class PretAMangerSpider(scrapy.Spider):
    name = "pret_a_manger"
    brands = {
        "Pret A Manger": {"brand": "Pret A Manger", "brand_wikidata": "Q2109109"},
        "Veggie Pret": {
            "brand": "Veggie Pret",
            "brand_wikidata": "Q108118332",
            "extras": {"amenity": "fast_food", "diet:vegetarian": "only"},
        },
    }

    start_urls = ["https://api1.pret.com/v1/shops"]

    def parse(self, response):
        for store in response.json()["shops"]:
            if not store["active"]:
                continue

            item = DictParser.parse(store)

            item["street_address"] = clean_address([item["housenumber"], item["street"]])
            item["housenumber"] = item["street"] = None

            oh = OpeningHours()
            for i in range(0, 7):
                rule = store["tradingHours"][i]
                if rule:
                    if rule in (["00:00", "00:00"], ["0:00AM", "0:00AM"], ["", ""]):
                        continue

                    if len(rule) != 2:
                        continue

                    if rule[0].startswith("0:"):
                        rule[0] = rule[0].replace("0:", "12:", 1)
                    if rule[1].startswith("0:"):
                        rule[1] = rule[1].replace("0:", "12:", 1)

                    oh.add_range(DAYS_3_LETTERS_FROM_SUNDAY[i], rule[0], rule[1], "%I:%M%p")

            item["opening_hours"] = oh.as_opening_hours()

            item["extras"] = {}

            item["extras"]["delivery"] = "yes" if store["features"].get("delivery") else "no"
            item["extras"]["storeType"] = store["features"].get("storeType")
            item["extras"]["wheelchair"] = "yes" if store["features"]["wheelchairAccess"] else "no"
            item["extras"]["internet_access"] = "wlan" if store["features"]["wifi"] else "no"

            if store["features"].get("storeType") == "veggie-pret":
                item.update(self.brands["Veggie Pret"])
            else:
                item.update(self.brands["Pret A Manger"])

            yield item
