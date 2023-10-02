from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider

CARREFOUR_SUPERMARKET = {
    "brand": "Carrefour",
    "brand_wikidata": "Q217599",
    "extras": Categories.SHOP_SUPERMARKET.value,
}

CARREFOUR_CONVENIENCE = {
    "brand": "Carrefour",
    "brand_wikidata": "Q217599",
    "extras": Categories.SHOP_CONVENIENCE.value,
}

CARREFOUR_MARKET = {
    "brand": "Carrefour Market",
    "brand_wikidata": "Q2689639",
    "extras": Categories.SHOP_SUPERMARKET.value,
}
CARREFOUR_CONTACT = {
    "brand": "Carrefour Contact",
    "brand_wikidata": "Q2940188",
    "extras": Categories.SHOP_SUPERMARKET.value,
}
CARREFOUR_EXPRESS = {
    "brand": "Carrefour Express",
    "brand_wikidata": "Q2940190",
    "extras": Categories.SHOP_CONVENIENCE.value,
}
CARREFOUR_CITY = {
    "brand": "Carrefour City",
    "brand_wikidata": "Q2940187",
    "extras": Categories.SHOP_SUPERMARKET.value,
}

class CarrefourFRSpider(WoosmapSpider):
    name = "carrefour_fr"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}

    key = "woos-26fe76aa-ff24-3255-b25b-e1bde7b7a683"
    origin = "https://www.carrefour.fr"

    brands = {
        "MARKET": CARREFOUR_MARKET,
        "CARREFOUR": CARREFOUR_CONVENIENCE,
        "CARREFOUR CITY": CARREFOUR_CITY,
        "CARREFOUR CONTACT": CARREFOUR_CONTACT,
        "CARREFOUR EXPRESS": CARREFOUR_EXPRESS,
        "CARREFOUR MARKET": CARREFOUR_MARKET,
        "CARREFOUR MONTAGNE": {
            "brand": "Carrefour Montagne",
            "brand_wikidata": "Q2940193",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
        "BON APP": {
            "brand": "Bon App!",
            "brand_wikidata": "Q90153100",
            "extras": Categories.SHOP_CONVENIENCE.value,
        }
    }

    def parse_item(self, item, feature, **kwargs):
        store_types = feature.get("properties").get("types", [])
        if len(store_types) > 0:
            if brand := self.brands.get(store_types[0]):
                item.update(brand)

            item["extras"]["store_type"] = store_types[0]
        # Unfortunately the "types" is often missing
        elif "Parapharmacie" in item["name"]:
            apply_category(Categories.PHARMACY, item)
        elif "Station Service Carrefour" in item["name"]:
            apply_category(Categories.FUEL_STATION, item)
        else:
            for brand in self.brands.values():
                if brand["brand"] in item["name"]:
                    item.update(brand)

        yield item
