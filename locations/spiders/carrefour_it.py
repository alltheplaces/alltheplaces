from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)


class CarrefourITSpider(Spider):
    name = "carrefour_it"
    start_urls = ["https://www.carrefour.it/on/demandware.store/Sites-carrefour-IT-Site/it_IT/StoreLocator-GetAll"]

    brands = {
        "iper": CARREFOUR_SUPERMARKET,
        "market": CARREFOUR_MARKET,
        "express": CARREFOUR_EXPRESS,
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
            if not self.brands.get(location["Type"]):
                self.crawler.stats.inc_value(f'atp/carrefour_it/unknown_brand/{location["Type"]}')
                continue

            parse_brand_and_category_from_mapping(item, location["Type"], self.brands)

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
