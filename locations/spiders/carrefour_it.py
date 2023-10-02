from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours


class CarrefourITSpider(Spider):
    name = "carrefour_it"
    start_urls = ["https://www.carrefour.it/on/demandware.store/Sites-carrefour-IT-Site/it_IT/StoreLocator-GetAll"]

    brands = {
        "iper": {"brand": "Carrefour", "brand_wikidata": "Q217599", "extras": Categories.SHOP_SUPERMARKET.value},
        "market": {
            "brand": "Carrefour Market",
            "brand_wikidata": "Q2689639",
            "extras": Categories.SHOP_SUPERMARKET.value,
        },
        "express": {
            "brand": "Carrefour Express",
            "brand_wikidata": "Q2940190",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
    }

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["name"] = location["Insegna"] + " " + location["Descrizione"]
            item["street_address"] = location["Indirizzo"]
            item["city"] = location["Citta"]
            item["state"] = location["Provincia"]
            item["postcode"] = location["CAP"]
            item["website"] = "https://www.carrefour.it" + location["Url"]
            item["opening_hours"] = OpeningHours()
            if location["Type"] not in self.brands.keys():
                continue
            item.update(self.brands[location["Type"]])
            for day_name, day_hours in location["Orari"].items():
                if day_hours.upper() == "CHIUSO":  # Closed
                    continue
                if "," in day_hours:
                    time_ranges = day_hours.split(",")
                    for time_range in time_ranges:
                        if len(time_range.split("-")) == 2:
                            item["opening_hours"].add_range(
                                DAYS_IT[day_name.title()], time_range.split("-", 1)[0], time_range.split("-", 1)[1]
                            )
                else:
                    if len(day_hours.split("-")) == 2:
                        item["opening_hours"].add_range(
                            DAYS_IT[day_name.title()], day_hours.split("-", 1)[0], day_hours.split("-", 1)[1]
                        )
            yield item
