import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingESPTSpider(scrapy.Spider):
    name = "burger_king_es_pt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://static.burgerkingencasa.es/bkhomewebsite/pt/stores_pt.json",
        "https://static.burgerkingencasa.es/bkhomewebsite/es/stores_es.json",
    ]

    def parse(self, response):
        for store in response.json()["stores"]:
            opening_hours = OpeningHours()

            always_closed = True
            for day in DAYS_FULL:
                opening_time = store[day.lower()]
                if opening_time is not None and opening_time != "CLOSED":
                    splits = opening_time.split(" - ")
                    if len(splits) == 1:
                        splits = opening_time.split("-")

                    open_time, close_time = splits
                    opening_hours.add_range(day, open_time, close_time)
                    always_closed = False

            url = response.url
            if url.endswith("stores_pt.json"):
                country = "PT"
            elif url.endswith("stores_es.json"):
                country = "ES"

            if not always_closed:
                item = DictParser.parse(store)

                item["ref"] = store["bkcode"]
                item["name"] = "Burger King"
                item["addr_full"] = store["address"]
                item["country"] = country
                item["opening_hours"] = opening_hours.as_opening_hours()
                item["extras"] = {
                    "drive_through": "yes" if store["autoking"] is True else "no",
                    "delivery": "yes" if store["delivery"] is True else "no",
                    "takeaway": "yes" if store["kiosko"] is True else "no",
                }
                yield item
