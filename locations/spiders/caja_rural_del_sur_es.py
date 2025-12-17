import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class CajaRuralDelSurESSpider(scrapy.Spider):
    name = "caja_rural_del_sur_es"
    item_attributes = {"brand": "Caja Rural del Sur", "brand_wikidata": "Q118719995"}
    allowed_domains = ["ruralvia.com"]
    start_urls = [
        "https://www.ruralvia.com/rviaoperations/rest/locator/office?codigoEntidad=3187&longitud=-3.7&latitud=40.4&radio=999&grupo=N"
    ]

    def parse(self, response):
        data = response.json()

        for location in data["response"]["data"]["ListaLocalizacion"]:
            item = Feature()
            item["ref"] = location["codigoOficina"]
            item["branch"] = location["nombreOficina"]
            item["street_address"] = location["direccion"]
            item["city"] = location["nombreLocalidad"]
            item["state"] = location["nombreProvincia"]
            item["postcode"] = location["codigoPostal"]
            item["lat"] = location["latitud"]
            item["lon"] = location["longitud"]
            item["phone"] = location.get("telefono")
            item["email"] = location.get("email") if location.get("email") else None

            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, location.get("indCajero") == "S")

            yield item
