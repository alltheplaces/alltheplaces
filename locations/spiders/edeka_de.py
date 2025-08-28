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

    # NO NSI Frischemarkt
    brands = {
        "nah&gut": {"name": "nah und gut", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "aktivmarkt": {"name": "Edeka aktiv markt", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "frischemarkt": {"name": "EDEKA Frischemarkt", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "trinkgut": {"name": "trinkgut", "brand": "trinkgut", "brand_wikidata": "Q2453627"},
        "scheckin": {"name": "Scheck-In Center", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "xpress": {"name": "Edeka xpress", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "diska": {"name": "diska", "brand": "diska", "brand_wikidata": "Q62390177"},
        "ecenterherkules": {"name": "HERKULES Ecenter", "brand": "HERKULES Ecenter", "brand_wikidata": "Q701755"},
        "edeka": {"name": "Edeka", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "ecenter": {"name": "E-Center", "brand": "Edeka", "brand_wikidata": "Q701755"},
        "marktkauf": {"name": "MARKTKAUF", "brand": "MARKTKAUF", "brand_wikidata": "Q1533254"},
        "capmarkt": {"name": "CAP-Markt", "brand": "CAP", "brand_wikidata": "Q1022827"},
        "npmarkt": {"name": "NP", "brand": "NP", "brand_wikidata": "Q15836148"},
        "marktbäckerei": {"name": "K&U Bäckerei", "brand": "K&U Bäckerei", "brand_wikidata": "Q1719433"},
        "ellimarkt": {"name": "Elli", "brand": "Elli", "brand_wikidata": "Q701755"},
    }

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

        brand_set = False
        for brand_key in self.brands.keys():
            if brand_key in name:
                brand_set = True
                item.update(self.brands[brand_key])
                break

        if "bäckerei" in name:
            apply_category(Categories.SHOP_BAKERY, item)
        elif "trinkgut" in name:
            apply_category(Categories.SHOP_BEVERAGES, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        if brand_set:
            branch = item.get("name")

            pattern = None
            if "nah&gut" in branch:
                pattern = r"^nah(?: und |&| & )gut (.+)$"
            elif "marktkauf" in branch:
                pattern = r"^Marktkauf(?:center)? (.+)$"
            elif "capmarkt" in branch:
                pattern = r"^CAP[ \-]Markt (.+)$"
            elif "ellimarkt" in branch:
                pattern = r"^Elli[ |-]Markt (.+)$"
            if pattern:
                if m := re.match(pattern, item["branch"], flags=re.IGNORECASE):
                    branch = m.group(1)

            item["branch"] = (
                branch.replace("diska ", "")
                .removeprefix("NP-Markt ")
                .removeprefix("Markt-Bäckerei ")
                .removeprefix("Frischemarkt ")
                .removeprefix("Scheck-in Center ")
                .removeprefix("trinkgut ")
            )
