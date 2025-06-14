from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)


class CarrefourITSpider(JSONBlobSpider):
    name = "carrefour_it"
    start_urls = ["https://www.carrefour.it/on/demandware.store/Sites-carrefour-IT-Site/it_IT/StoreLocator-GetAll"]
    locations_key = "stores"

    brands = {
        "iper": CARREFOUR_SUPERMARKET,
        "market": CARREFOUR_MARKET,
        "express": CARREFOUR_EXPRESS,
    }

    def post_process_item(self, item, response, location):
        item["name"] = location["Insegna"] + " " + location["Descrizione"]
        item["street_address"] = location["Indirizzo"]
        item["city"] = location["Citta"]
        item["state"] = location["Provincia"]
        item["postcode"] = location["CAP"]
        item["website"] = "https://www.carrefour.it" + location["Url"]
        if not self.brands.get(location["Type"]):
            self.crawler.stats.inc_value(f'atp/carrefour_it/unknown_brand/{location["Type"]}')
            return

        parse_brand_and_category_from_mapping(item, location["Type"], self.brands)

        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in location["Orari"].items():
            item["opening_hours"].add_ranges_from_string(
                f"{day_name} {day_hours}",
                days=DAYS_IT,
                closed=CLOSED_IT,
            )
        yield item
