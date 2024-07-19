import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

FUEL_TYPES_MAPPING = {
    "AdBlue": Fuel.ADBLUE,
    "Alkylat": Fuel.ALKYLATE,
    "Bensin 95": Fuel.OCTANE_95,
    "Bensin 98": Fuel.OCTANE_98,
    "Biogas": Fuel.BIOGAS,
    "Diesel": Fuel.DIESEL,
    "E85": Fuel.E85,
    "HVO100": Fuel.BIODIESEL,
    "RME": Fuel.BIODIESEL,
}

BRANDS_MAPPING = {
    "Qstar": {"brand": "Qstar", "brand_wikidata": "Q10647961"},
    "Pump": {"brand": "Pump"},
    "Bilisten": {"brand": "Bilisten"},
}


class QstarSESpider(scrapy.Spider):
    name = "qstar_se"
    start_urls = ["https://qstar-backend-prod.herokuapp.com/api/v2/stations/qstar"]

    def parse(self, response, **kwargs):
        for store in response.json():
            store.pop("zip")  # It's not a postcode
            item = DictParser.parse(store)
            if item.get("city"):
                # When city is present the address is street_address
                item["street_address"] = item.pop("addr_full")

            if match := BRANDS_MAPPING.get(store.get("brand", {})):
                item["brand"] = match.get("brand")
                item["brand_wikidata"] = match.get("brand_wikidata")

            for fuel in store.get("products", "").split(", "):
                if tag := FUEL_TYPES_MAPPING.get(fuel):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"qstar_se/fuel/fail/{fuel}")

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.CAR_WASH, item, store.get("carWash") is not None)
            yield item
