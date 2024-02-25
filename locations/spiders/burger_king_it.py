import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingItSpider(scrapy.Spider):
    name = "burger_king_it"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.it/api/data/it/ristoranti.json"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = store["storeId"]
            item["name"] = "Burger King"
            item["addr_full"] = store["address"]
            item["city"] = store["name"]
            item["country"] = "IT"
            item["extras"] = {
                "internet_access": "wlan" if "WIFI" in store["servizi"] else "no",
                "drive_through": "yes" if "KingDrive" in store["servizi"] else "no",
                "delivery": "yes" if "HomeDelivery" in store["servizi"] else "no",
            }

            item["opening_hours"] = OpeningHours()
            for day_name, hours in store["orari"]["ristorante"].items():
                if hours["lunch_end"] and hours["dinner_start"]:
                    item["opening_hours"].add_range(DAYS_IT[day_name.title()], hours["lunch_start"], hours["lunch_end"])
                    item["opening_hours"].add_range(
                        DAYS_IT[day_name.title()], hours["dinner_start"], hours["dinner_end"]
                    )
                else:
                    item["opening_hours"].add_range(
                        DAYS_IT[day_name.title()], hours["lunch_start"], hours["dinner_end"]
                    )

            yield item
