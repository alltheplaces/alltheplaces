import scrapy
from scrapy import Request

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class EdekaDESpider(scrapy.Spider):
    name = "edeka_de"
    start_urls = ["https://www.edeka.de/api/marketsearch/markets?size=100"]

    NAH_UND_GUT = {"brand": "nah und gut", "brand_wikidata": "Q701755", "extras": Categories.SHOP_SUPERMARKET.value}
    AKTIV_MARKT = {
        "brand": "EDEKA aktiv markt",
        "brand_wikidata": "Q701755",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    XPRESS = {"brand": "EDEKA xpress", "brand_wikidata": "Q701755", "extras": Categories.SHOP_SUPERMARKET.value}
    DISKA = {"brand": "diska", "brand_wikidata": "Q62390177", "extras": Categories.SHOP_SUPERMARKET.value}
    EDEKA = {"brand": "EDEKA", "brand_wikidata": "Q701755", "extras": Categories.SHOP_SUPERMARKET.value}
    ECENTER = {"brand": "E-Center", "brand_wikidata": "Q701755", "extras": Categories.SHOP_SUPERMARKET.value}
    ECENTER_HERKULES = {
        "brand": "HERKULES Ecenter",
        "brand_wikidata": "Q701755",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    MARKTKAUF = {"brand": "MARKTKAUF", "brand_wikidata": "Q1533254"}
    CAPMARKT = {"brand": "CAP", "brand_wikidata": "Q1022827"}
    NPMARKT = {"brand": "NP", "brand_wikidata": "Q15836148"}
    MARKT_BACKEREI = {"brand": "Markt-Bäckerei", "brand_wikidata": "Q1719433"}
    ELLI = {"brand": "Elli", "brand_wikidata": "Q701755", "extras": Categories.SHOP_SUPERMARKET.value}

    def parse(self, response):
        for store in response.json()["markets"]:
            store.update(store.pop("contact"))
            store["address"]["postcode"] = store["address"]["city"]["zipCode"]
            store["address"]["city"] = store["address"]["city"]["name"]
            store["address"]["street_address"] = store["address"].pop("street")
            store["address"]["state"] = store["address"]["federalState"]

            item = DictParser.parse(store)

            item["opening_hours"] = self.parse_hours(store)

            name = item["name"].lower().replace(" ", "").replace("und", "&").replace("-", "")
            if "nah&gut" in name:
                item.update(self.NAH_UND_GUT)
            elif "aktivmarkt" in name:
                item.update(self.AKTIV_MARKT)
            elif "xpress" in name:
                item.update(self.XPRESS)
            elif "diska" in name:
                item.update(self.DISKA)
            elif "edeka" in name:
                item.update(self.EDEKA)
            elif "ecenterherkules" in name:
                item.update(self.ECENTER_HERKULES)
            elif "ecenter" in name:
                item.update(self.ECENTER)
            elif "marktkauf" in name:
                item.update(self.MARKTKAUF)
            elif "capmarkt" in name:
                item.update(self.CAPMARKT)
            elif "npmarkt" in name:
                item.update(self.NPMARKT)
            elif "marktbäckerei" in name:
                item.update(self.MARKT_BACKEREI)
            elif "ellimarkt" in name:
                item.update(self.ELLI)
            else:
                item.update(self.EDEKA)
            if item["website"] == "https://www.edeka.de/eh/minden-hannover/edeka-junghans-poppauer-str.-2/index.jspp":
                item["website"] = "https://www.edeka.de/eh/minden-hannover/edeka-junghans-poppauer-str.-2/index.jsp"
            yield item

        if next := response.json()["_links"].get("next"):
            yield Request(url=f'https://www.edeka.de{next["href"]}')

    def parse_hours(self, store_obj):
        oh = OpeningHours()
        for day in store_obj["businessHours"].values():
            if not isinstance(day, dict) or not day["open"]:
                continue

            for rule in day["timeEntries"]:
                oh.add_range(day["weekday"], rule["from"], rule["to"])

        return oh
