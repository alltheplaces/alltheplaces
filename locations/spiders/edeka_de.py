import re
from typing import Any

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class EdekaDESpider(scrapy.Spider):
    name = "edeka_de"
    start_urls = ["https://www.edeka.de/api/marketsearch/markets?size=100"]

    NAH_UND_GUT = {"name": "nah und gut", "brand": "Edeka", "brand_wikidata": "Q701755"}
    AKTIV_MARKT = {"name": "Edeka aktiv markt", "brand": "Edeka", "brand_wikidata": "Q701755"}
    XPRESS = {"name": "Edeka xpress", "brand": "Edeka", "brand_wikidata": "Q701755"}
    DISKA = {"brand": "diska", "brand_wikidata": "Q62390177"}
    EDEKA = {"name": "Edeka", "brand": "Edeka", "brand_wikidata": "Q701755"}
    ECENTER = {"name": "E-Center", "brand": "Edeka", "brand_wikidata": "Q701755"}
    ECENTER_HERKULES = {"name": "HERKULES Ecenter", "brand": "HERKULES Ecenter", "brand_wikidata": "Q701755"}
    MARKTKAUF = {"brand": "MARKTKAUF", "brand_wikidata": "Q1533254"}
    CAPMARKT = {"brand": "CAP", "brand_wikidata": "Q1022827"}
    NPMARKT = {"brand": "NP", "brand_wikidata": "Q15836148"}
    MARKT_BACKEREI = {"brand": "K&U Bäckerei", "brand_wikidata": "Q1719433"}
    ELLI = {"name": "Elli", "brand": "Elli", "brand_wikidata": "Q701755"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["markets"]:
            store.update(store.pop("contact"))
            store["address"]["postcode"] = store["address"]["city"]["zipCode"]
            store["address"]["city"] = store["address"]["city"]["name"]
            store["address"]["street_address"] = store["address"].pop("street")
            store["address"]["state"] = store["address"]["federalState"]

            item = DictParser.parse(store)

            item["opening_hours"] = self.parse_hours(store)

            self.apply_branding(item)

            yield item

        if next_page := response.json()["_links"].get("next"):
            yield Request(response.urljoin(next_page["href"]))

    def parse_hours(self, store_obj):
        oh = OpeningHours()
        for day in store_obj["businessHours"].values():
            if not isinstance(day, dict) or not day["open"]:
                continue

            for rule in day["timeEntries"]:
                oh.add_range(day["weekday"], rule["from"], rule["to"])

        return oh

    def apply_branding(self, item: Feature):
        name = item["name"].lower().replace(" ", "").replace("und", "&").replace("-", "")

        if "nah&gut" in name:
            if m := re.match(r"^nah(?: und |&| & )gut (.+)$", item.pop("name"), flags=re.IGNORECASE):
                item["branch"] = m.group(1)
            item.update(self.NAH_UND_GUT)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "aktivmarkt" in name:
            item.update(self.AKTIV_MARKT)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "xpress" in name:
            item.update(self.XPRESS)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "diska" in name:
            item["branch"] = item.pop("name").removeprefix("diska ")
            item.update(self.DISKA)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "edeka" in name:
            item.update(self.EDEKA)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "ecenterherkules" in name:
            item.update(self.ECENTER_HERKULES)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "ecenter" in name:
            item.update(self.ECENTER)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "marktkauf" in name:
            if m := re.match(r"^Marktkauf(?:center)? (.+)$", item.pop("name"), flags=re.IGNORECASE):
                item["branch"] = m.group(1)
            item.update(self.MARKTKAUF)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "capmarkt" in name:
            if m := re.match(r"^CAP[ \-]Markt (.+)$", item.pop("name"), flags=re.IGNORECASE):
                item["branch"] = m.group(1)
            item.update(self.CAPMARKT)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "npmarkt" in name:
            item["branch"] = item.pop("name").removeprefix("NP-Markt ")
            item.update(self.NPMARKT)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "marktbäckerei" in name:
            item["branch"] = item.pop("name").removeprefix("Markt-Bäckerei ")
            item.update(self.MARKT_BACKEREI)
            apply_category(Categories.SHOP_BAKERY, item)
        elif "ellimarkt" in name:
            if m := re.match(r"^Elli[ |-]Markt (.+)$", item.pop("name"), flags=re.IGNORECASE):
                item["branch"] = m.group(1)
            item.update(self.ELLI)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            self.logger.info(f"Unknown store: {item['name']}")
