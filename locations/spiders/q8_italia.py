from scrapy import Spider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature

# Ref: https://www.q8.it/geolocalizzatore/js/storelocator/managefilter.js?v":2.0.16
FUEL_TYPES_MAPPING = {
    "300004": Fuel.OCTANE_95,  # COD_BENZINA
    "300016": Fuel.DIESEL,  # COD_DIESEL
    "300391": Fuel.DIESEL,  # COD_HIQ
    "300054": Fuel.LPG,  # COD_GPL
    "301403": Fuel.OCTANE_99,  # COD_BENZINA_VPOWER99
    "301404": Fuel.OCTANE_100,  # COD_HI_PERFORM_100OTTANI
    "301362": Fuel.DIESEL,  # COD_VPOWER_DIESEL
    "300991": Fuel.ADBLUE,  # COD_ADBLUE
    "301793": Fuel.ADBLUE,  # COD_ADBLUE_NEW
    "301471": Fuel.CNG,  # COD_METANO1
    "302043": Fuel.CNG,  # COD_METANO2
    "302042": Fuel.LNG,  # COD_METANO_LNG
    "400011": Fuel.OCTANE_95,  # COD_GASOLINA_95
    "400012": Fuel.OCTANE_98,  # COD_GASOLINA_98
    "400013": Fuel.DIESEL,  # COD_GASOLEO_A
    "400014": Fuel.DIESEL,  # COD_GASOLEO_B
    "400015": Fuel.DIESEL,  # COD_GASOLEO_C
    "400016": Fuel.DIESEL,  # COD_GASOLEO_HIQ
    "400017": Fuel.ADBLUE,  # ADBLUE_SPAIN":
    "302182": Fuel.BIODIESEL,  # COD_HVO_PLUS
    # TODO: figure out below fuels
    "300015": None,  # COD_GASOLIO_AGRICOLO
    "300018": None,  # COD_GASOLIO_ARTICO
    "000000": None,  # COD_ALTRO
    # "400060": 262,
    # "F20020100": 34,
    # "F30201713": 314,
    # "F30201903": 315,
    # "F40400303": 316,
    # "F40400313": 205,
    # "F41767000": 91,
}

# Confusingly, not just IT but most of Europe
# Also not just Q8Italia


class Q8ItaliaSpider(Spider):
    name = "q8_italia"
    item_attributes = {"brand": "Q8", "brand_wikidata": "Q1634762"}
    start_urls = ["https://www.q8.it/geolocalizzatore/pv/all"]

    BRANDS = {
        "TANGO": None,  # TangoSpider
        "AUTOMAT": {"brand": "Q8 Easy", "brand_wikidata": "Q1806948"},
        # All others Q8
    }

    def parse(self, response, **kwargs):
        for location in response.json():
            # Note more? details available at:
            # https://www.q8.it/geolocalizzatore/pv/00PV000158

            item = Feature()
            item["ref"] = location["codice"]
            item["street_address"] = location["indirizzo"]
            item["city"] = location["localita"]
            item["state"] = location["provincia"]
            item["postcode"] = location["cap"]
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]

            b = location["tipologie"][0]["tipologia"]
            if b == "TANGO":
                continue  # Throw away Tango POIs as duplicates data from TangoSpider

            if brand := self.BRANDS.get(b):
                item.update(brand)

            # TODO: payments
            # pagamenti
            # digitali
            # sblocco
            # TODO: services
            # servizi

            self.parse_fuel(item, location)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_fuel(self, item, location):
        for products in location.get("prodotti", []):
            product_code = products.get("codiceProdotto")
            if tag := FUEL_TYPES_MAPPING.get(product_code):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/q8_italia/unknown_fuel_type/{product_code}")
