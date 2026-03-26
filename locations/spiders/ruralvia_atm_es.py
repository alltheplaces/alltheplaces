from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.items import Feature

BRAND_MAPPING = {
    "CAJA RURAL DEL SUR": ("Caja Rural del Sur", "Q118719995"),
    "CAJAMAR": ("Cajamar", "Q8254971"),
    "BANKINTER": ("Bankinter", "Q806808"),
    "DEUTSCHE BANK": ("Deutsche Bank", "Q66048"),
    "CAJA RURAL DE GRANADA": ("Caja Rural de Granada", "Q5739400"),
    "CAJASIETE": ("Cajasiete", "Q5739505"),
    "EURONET": ("Euronet", "Q5412010"),
    "GLOBALCAJA": ("Globalcaja", "Q9263817"),
    "CAJA RURAL DE JAÉN": ("Caja Rural de Jaén", "Q18720350"),
    "CAJA RURAL DE JAEN": ("Caja Rural de Jaén", "Q18720350"),  # Typo variant
    "CAJA RURAL DE SALAMANCA": ("Caja Rural de Salamanca", "Q106928223"),
    "CAJA RURAL DE EXTREMADURA": ("Caja Rural de Extremadura", "Q118720015"),
    "CAIXA RURAL GALEGA": ("Caixa Rural Galega", "Q12384941"),
    "CAJA RURAL DE ZAMORA": ("Caja Rural de Zamora", "Q118719984"),
    "ARQUIA": ("Arquia Banca", "Q20104130"),
    "CAJAVIVA CAJA RURAL": ("Cajaviva Caja Rural", "Q118720026"),
    "CAJA RURAL DE SORIA": ("Caja Rural de Soria", "Q118719955"),
    "CAJA RURAL DE NAVARRA": ("Caja Rural de Navarra", "Q73399877"),
    "CAJA RURAL DE ARAGON": ("Caja Rural de Aragón", "Q5719155"),
}


class RuralviaAtmESSpider(Spider):
    name = "ruralvia_atm_es"
    allowed_domains = ["ruralvia.com"]

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "ES"):
            url = f"https://www.ruralvia.com/rviaoperations/rest/locator/cashier?codigoEntidad=3187&longitud={lon}&latitud={lat}&radio=20"
            yield Request(url, callback=self.parse)

    def parse(self, response):
        data = response.json()

        # Some locations may not have any ATMs
        if "ListaCajeros" not in data.get("response", {}).get("data", {}):
            return

        atm_data = data["response"]["data"]["ListaCajeros"]
        # API returns a dict for single ATM, list for multiple ATMs
        if isinstance(atm_data, dict):
            atm_data = [atm_data]

        for location in atm_data:
            item = Feature()

            entity_name = location["nombreEntidad"]
            if entity_name in BRAND_MAPPING:
                item["brand"], item["brand_wikidata"] = BRAND_MAPPING[entity_name]
            else:
                item["brand"] = entity_name

            item["ref"] = location.get("codigoCajeros")
            item["street_address"] = location["direccion"]
            item["city"] = location["nombreLocalidad"]
            item["postcode"] = location["codigoPostal"]
            item["lat"] = location["latitud"]
            item["lon"] = location["longitud"]

            apply_category(Categories.ATM, item)

            yield item
