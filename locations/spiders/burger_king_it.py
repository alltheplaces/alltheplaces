import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_IT


class BurgerKingItSpider(scrapy.Spider):
    name = 'burger_king_it'
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}
    start_urls = [
        'https://burgerking.it/api/data/it/ristoranti.json',
    ]

    def parse(self, response):
        for store in response.json():
            opening_hours = OpeningHours()

            opening_time = store["orari"]["ristorante"]
            for d in DAYS_IT:
                opening_hours.add_range(DAYS_IT[d],
                                        opening_time[d.lower()]["lunch_start"],
                                        opening_time[d.lower()]["dinner_end"])

            item = DictParser.parse(store)

            item["ref"] = store["storeId"]
            item["name"] = "Burger King"
            item["addr_full"] = store["address"]
            item["city"] = store["name"]
            item["country"] = "IT"
            item["opening_hours"] = opening_hours.as_opening_hours()
            item["extras"] = {
                "internet_access": "wlan" if "WIFI" in store["servizi"] else "no",
                "drive_through": "yes" if "KingDrive" in store["servizi"] else "no",
                "delivery": "yes" if "HomeDelivery" in store["servizi"] else "no",
            }
            yield item
