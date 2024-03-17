import scrapy
import xmltodict

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.carrefour_fr import CARREFOUR_EXPRESS, CARREFOUR_MARKET, CARREFOUR_SUPERMARKET

CARREFOUR_BIO = {
    "brand": "Carrefour BIO",
    "brand_wikidata": "Q55221138",
    "category": Categories.SHOP_SUPERMARKET,
}
CARREFOUR_VIAJES = {
    "brand": "Carrefour Viajes",
    "brand_wikidata": "Q116483791",
    "category": Categories.SHOP_TRAVEL_AGENCY,
}


class CarrefourESSpider(scrapy.Spider):
    name = "carrefour_es"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}
    brands = {
        "hipermercado": CARREFOUR_SUPERMARKET,
        "market": CARREFOUR_MARKET,
        "express": CARREFOUR_EXPRESS,
        "bio": CARREFOUR_BIO,
        "agencia de viajes": CARREFOUR_VIAJES,
    }
    start_urls = ["https://www.carrefour.es/tiendas-carrefour/buscador-de-tiendas/locations.aspx"]
    no_refs = True

    def parse(self, response, **kwargs):
        for store_data in xmltodict.parse(response.text)["markers"]["marker"]:
            store = {key.removeprefix("@"): value for key, value in store_data.items()}
            store["street-address"] = merge_address_lines([store.pop("address", ""), store.pop("address2", "")])
            item = DictParser.parse(store)
            item["website"] = response.urljoin(store["web"]) if store.get("web") else response.url
            location_category = store.get("category", "").lower()
            if "estación de servicio" in location_category:
                apply_category(Categories.FUEL_STATION, item)
            else:
                for brand_key, brand_info in self.brands.items():
                    if brand_key in location_category:
                        item["brand"] = brand_info["brand"]
                        item["brand_wikidata"] = brand_info["brand_wikidata"]
                        apply_category(brand_info["category"], item)
                        break
            if "cepsa" in location_category:
                item["located_in"] = "Cepsa"
                item["located_in_wikidata"] = "Q608819"
            if services := store.get("features", "").lower():
                apply_yes_no(Extras.ATM, item, "cajeros automáticos" in services)
                apply_yes_no(Extras.WIFI, item, "wifi gratis" in services)
                apply_yes_no(Extras.DELIVERY, item, "entrega a domicilio" in services)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "carrefour drive" in services)
                apply_yes_no(Extras.SELF_CHECKOUT, item, "cajas de autopago" in services)
                apply_yes_no(Extras.CAR_WASH, item, "lavado de coches" in services)
                apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "cambiador de bebé" in services)
                apply_yes_no("amenity:parking", item, "aparcamiento" in services)
                # TODO: more services

            yield item
