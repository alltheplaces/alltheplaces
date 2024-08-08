from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider

CARREFOUR_SUPERMARKET = {
    "brand": "Carrefour",
    "brand_wikidata": "Q217599",
    "category": Categories.SHOP_SUPERMARKET,
}

CARREFOUR_CONVENIENCE = {
    "brand": "Carrefour",
    "brand_wikidata": "Q217599",
    "category": Categories.SHOP_CONVENIENCE,
}

CARREFOUR_MARKET = {
    "brand": "Carrefour Market",
    "brand_wikidata": "Q2689639",
    "category": Categories.SHOP_SUPERMARKET,
}
CARREFOUR_CONTACT = {
    "brand": "Carrefour Contact",
    "brand_wikidata": "Q2940188",
    "category": Categories.SHOP_SUPERMARKET,
}
CARREFOUR_EXPRESS = {
    "brand": "Carrefour Express",
    "brand_wikidata": "Q2940190",
    "category": Categories.SHOP_CONVENIENCE,
}
CARREFOUR_CITY = {
    "brand": "Carrefour City",
    "brand_wikidata": "Q2940187",
    "category": Categories.SHOP_SUPERMARKET,
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
            "category": Categories.SHOP_CONVENIENCE,
        },
        "BON APP": {
            "brand": "Bon App!",
            "brand_wikidata": "Q90153100",
            "category": Categories.SHOP_CONVENIENCE,
        },
    }

    def parse_item(self, item, feature, **kwargs):
        store_types = feature.get("properties").get("types", [])
        if store_types:
            parse_brand_and_category_from_mapping(item, store_types[0], self.brands)
            item["extras"]["store_type"] = store_types[0]
        # Unfortunately the "types" is often missing
        elif "Parapharmacie" in item["name"]:
            apply_category(Categories.PHARMACY, item)
        elif "Station Service Carrefour" in item["name"]:
            apply_category(Categories.FUEL_STATION, item)
        else:
            for brand in self.brands.values():
                if brand["brand"] in item["name"]:
                    item["brand"] = brand.get("brand")
                    item["brand_wikidata"] = brand.get("brand_wikidata")
                    apply_category(brand.get("category"), item)
                    break
            else:
                # default to supermarket
                apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item


def parse_brand_and_category_from_mapping(item: Feature, brand_key: str, brand_mapping: dict):
    if match := brand_mapping.get(brand_key):
        item["brand"] = match.get("brand")
        item["brand_wikidata"] = match.get("brand_wikidata")
        apply_category(match.get("category"), item)
        return True
    return False
