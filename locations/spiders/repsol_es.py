import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS_EN, DAYS_ES, OpeningHours
from locations.items import Feature


class RepsolESSpider(Spider):
    name = "repsol_es"
    item_attributes = {"brand": "Repsol", "brand_wikidata": "Q174747"}
    allowed_domains = ["www.repsol.es"]
    start_urls = ["https://www.repsol.es/bin/repsol/searchmiddleware/station-search.json?action=search&tipo=1,2"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST")

    def parse(self, response):
        for location in response.json()["eess"]["items"]:
            properties = {
                "ref": location.get("id"),
                "name": location.get("nombre"),
                "lat": location.get("y"),
                "lon": location.get("x"),
                "street_address": location.get("direccion"),
                "city": location.get("localidad"),
                "state": location.get("provincia"),
                "postcode": location.get("cp"),
                "phone": location.get("telefono"),
            }

            properties["opening_hours"] = OpeningHours()
            for day_hours in location.get("horarios"):
                if day_hours["dia"].title() in DAYS_ES:
                    day = DAYS_ES[day_hours["dia"].title()]
                elif day_hours["dia"].title() in DAYS_EN:
                    day = DAYS_EN[day_hours["dia"].title()]
                else:
                    continue
                for hours_range in day_hours["horario"].split(","):
                    if m := re.findall(r"(\d{2}:\d{2}(?!:)|\d{2}:\d{2}(?=:\d{2}))", hours_range):
                        properties["opening_hours"].add_range(day, m[0], m[1], "%H:%M")

            apply_category(Categories.FUEL_STATION, properties)
            products = [x["producto"] for x in location["productos"]]
            apply_yes_no(
                Fuel.OCTANE_95,
                properties,
                "Efitec 95" in products or "S/CHUMBO 95" in products or "Efitec 95 Premium" in products,
                False,
            )
            apply_yes_no(Fuel.OCTANE_98, properties, "Efitec 98" in products, False)
            apply_yes_no(
                Fuel.BUTANE,
                properties,
                "Butano 12,5 Kg" in products or "Butano 12 Kg (NEL)" in products or "Butano 6 Kg (K6)" in products,
                False,
            )
            apply_yes_no(Fuel.PROPANE, properties, "Propano 11 Kg" in products, False)
            apply_yes_no(Fuel.DIESEL, properties, "Diésel e+" in products or "GASÓLEO" in products, False)
            apply_yes_no(Fuel.GTL_DIESEL, properties, "Diésel e+10" in products, False)
            apply_yes_no(Fuel.UNTAXED_DIESEL, properties, "Gasóleo B" in products, False)
            apply_yes_no(Fuel.LPG, properties, "Autogás" in products, False)
            apply_yes_no(Fuel.ADBLUE, properties, "Blue+" in products, False)

            yield Feature(**properties)
