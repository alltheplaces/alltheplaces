from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import point_locations
from locations.items import Feature


class RuralviaESSpider(Spider):
    name = "ruralvia_es"
    allowed_domains = ["ruralvia.com"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    # Mapping of entity codes to brand names and wikidata IDs
    BRANDS = {
        "0198": {"brand": "Banco Cooperativo Español", "brand_wikidata": "Q118733226"},
        "3005": {"brand": "Caja Rural Central", "brand_wikidata": "Q118720020"},
        "3007": {"brand": "Caja Rural de Gijón", "brand_wikidata": "Q118720010"},
        "3008": {"brand": "Caja Rural de Navarra", "brand_wikidata": "Q73399877"},
        "3009": {"brand": "Caja Rural de Extremadura", "brand_wikidata": "Q118720015"},
        "3016": {"brand": "Caja Rural de Salamanca", "brand_wikidata": "Q106928223"},
        "3017": {"brand": "Caja Rural de Soria", "brand_wikidata": "Q118719955"},
        "3018": {"brand": "Caja Rural San Agustín de Fuente Álamo", "brand_wikidata": "Q118720001"},
        "3020": {"brand": "Caja Rural de Utrera", "brand_wikidata": None},  # No Wikidata ID
        "3023": {"brand": "Caja Rural de Granada", "brand_wikidata": "Q5739400"},
        "3059": {"brand": "Caja Rural de Asturias", "brand_wikidata": "Q5739398"},
        "3060": {"brand": "Caja Rural de Burgos", "brand_wikidata": None},  # No Wikidata ID
        "3067": {"brand": "Caja Rural de Jaén", "brand_wikidata": "Q18720350"},
        "3070": {"brand": "Caixa Rural Galega", "brand_wikidata": "Q12384941"},
        "3076": {"brand": "Cajasiete", "brand_wikidata": "Q5739505"},
        "3080": {"brand": "Caja Rural de Teruel", "brand_wikidata": "Q5739403"},
        "3081": {"brand": "Eurocaja Rural", "brand_wikidata": "Q57496866"},
        "3085": {"brand": "Caja Rural de Zamora", "brand_wikidata": "Q118719984"},
        "3089": {"brand": "Caja Rural de Baena", "brand_wikidata": None},  # No Wikidata ID
        "3096": {"brand": "Caixa Rural de l'Alcúdia", "brand_wikidata": "Q118720009"},
        "3098": {"brand": "Caja Rural de Nueva Carteya", "brand_wikidata": None},  # No Wikidata ID
        "3104": {"brand": "Caja Rural de Cañete de las Torres", "brand_wikidata": None},  # No Wikidata ID
        "3111": {"brand": "Caixa Rural La Vall", "brand_wikidata": None},  # No Wikidata ID
        "3113": {"brand": "Caja Rural San José de Alcora", "brand_wikidata": "Q118720036"},
        "3115": {"brand": "Caja Rural Nuestra Madre del Sol", "brand_wikidata": None},  # No Wikidata ID
        "3117": {"brand": "Caixa Rural d'Algemesí", "brand_wikidata": "Q118720032"},
        "3127": {"brand": "Caja Rural de Casas Ibáñez", "brand_wikidata": "Q118720023"},
        "3130": {"brand": "Caja Rural San José de Almassora", "brand_wikidata": "Q112614206"},
        "3134": {"brand": "Caja Rural Onda", "brand_wikidata": "Q118720002"},
        "3138": {"brand": "Ruralnostra", "brand_wikidata": "Q118720029"},
        "3144": {"brand": "Caja Rural de Villamalea", "brand_wikidata": "Q118719986"},
        "3159": {"brand": "Caixa Popular", "brand_wikidata": "Q8254944"},
        "3162": {"brand": "Caixa Rural Benicarló", "brand_wikidata": "Q118733003"},
        "3166": {"brand": "Caixa Rural Les Coves de Vinromà", "brand_wikidata": "Q118720017"},
        "3174": {"brand": "Caixa Rural Vinaròs", "brand_wikidata": "Q118719993"},
        "3187": {"brand": "Caja Rural del Sur", "brand_wikidata": "Q118719995"},
        "3190": {"brand": "Caja Rural de Albacete", "brand_wikidata": "Q18223400"},  # Operates as Globalcaja
        "3191": {"brand": "Caja Rural de Aragón", "brand_wikidata": "Q5719155"},
    }

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "ES"):
            yield Request(
                f"https://www.ruralvia.com/rviaoperations/rest/locator/office?codigoEntidad=9998&longitud={lon}&latitud={lat}&radio=120&grupo=S"
            )

    def parse(self, response):
        data = response.json()

        for location in data["response"]["data"]["ListaLocalizacion"]:
            entity_code = location.get("codigoEntidad")
            brand_info = self.BRANDS.get(entity_code)

            if not brand_info:
                self.logger.warning(f"Unknown entity code: {entity_code} - {location.get('nombreEntidad')}")
                continue

            item = Feature()
            item["ref"] = f"{entity_code}_{location['codigoOficina']}"
            item["branch"] = location["nombreOficina"]
            item["street_address"] = location["direccion"]
            item["city"] = location["nombreLocalidad"]
            item["state"] = location["nombreProvincia"]
            item["postcode"] = location["codigoPostal"]
            item["lat"] = location["latitud"]
            item["lon"] = location["longitud"]
            item["phone"] = location.get("telefono")
            item["email"] = location.get("email") if location.get("email") else None

            item["brand"] = brand_info["brand"]
            item["brand_wikidata"] = brand_info["brand_wikidata"]

            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, location.get("indCajero") == "S")

            yield item
