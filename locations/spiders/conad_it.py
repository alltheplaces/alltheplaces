from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature


class ConadITSpider(Spider):
    name = "conad_it"

    brands = {
        "CONAD": {"brand": "Conad", "brand_wikidata": "Q639075"},
        "CONAD CITY": {"brand": "Conad City", "brand_wikidata": "Q57543102"},
        "CONAD SELF 24h": {"brand": "Conad", "brand_wikidata": None, "extras": Categories.FUEL_STATION.value},
        "CONAD SUPERSTORE": {"brand": "Conad Superstore", "brand_wikidata": "Q118129616"},
        "MARGHERITA CONAD": {
            "brand": "Margherita Conad",
            "brand_wikidata": None,
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
        "MARKET CONAD": {"brand": "Conad", "brand_wikidata": "Q639075"},
        "PARAFARMACIA CONAD": {
            "brand": "Parafarmacia Conad",
            "brand_wikidata": None,
            "extras": Categories.PHARMACY.value,
        },
        "PET STORE CONAD": {"brand": "Petstore", "brand_wikidata": None, "extras": Categories.SHOP_PET.value},
        "SAPORI & DINTORNI CONAD": {
            "brand": "Sapori & Dintorni Conad",
            "brand_wikidata": None,
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
        "SPAZIO CONAD": {"brand": "Spazio Conad", "brand_wikidata": "Q118130063"},
        "SPESA FACILE": {"brand": "Spesa Facile", "brand_wikidata": None, "extras": Categories.SHOP_CONVENIENCE.value},
        "TUDAY CONAD": {"brand": "Tuday Conad", "brand_wikidata": None, "extras": Categories.SHOP_CONVENIENCE.value},
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://www.conad.it/api/corporate/it-it.retrievePointOfService.json",
            headers={"Referer": "https://www.conad.it/ricerca-negozi"},
            data={
                "latitudine": "0",
                "longitudine": "0",
                "raggioRicerca": "15000",
                "insegneId": [],
                "serviziId": [],
                "repartiId": [],
                "apertura": [],
            },
        )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = Feature()
            item["ref"] = location["id"]
            item["street_address"] = location["indirizzo"]
            item["phone"] = location["telefono"]
            item["postcode"] = location["cap"]
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]
            item["state"] = location["codiceProvincia"]
            item["website"] = location["pdvLink"]["plainHref"]
            item["addr_full"] = location["pdvUrlAddress"]

            if brand := self.brands.get(location["descrizioneInsegna"]):
                item.update(brand)
            else:
                item["brand"] = location["descrizioneInsegna"]

            item["opening_hours"] = OpeningHours()
            for rule in location["giornateOrdinarie"]:
                if day := sanitise_day(rule["giornoSettimana"], DAYS_IT):
                    if rule.get("chiusuraMattina") and rule.get("aperturaPomeriggio"):
                        # Morning and afternoon
                        item["opening_hours"].add_range(day, rule["aperturaMattina"], rule["chiusuraMattina"])
                        item["opening_hours"].add_range(day, rule["aperturaPomeriggio"], rule["chiusuraPomeriggio"])
                    else:
                        # Just 1 time range
                        item["opening_hours"].add_range(day, rule["aperturaMattina"], rule["chiusuraPomeriggio"])

            yield item
