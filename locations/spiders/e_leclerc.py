from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider


class ELeclercSpider(WoosmapSpider):
    name = "e_leclerc"
    item_attributes = {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"}
    key = "woos-6256d36f-af9b-3b64-a84f-22b2342121ba"
    origin = "https://www.e.leclerc"

    brands = {
        "Jardi": ({"brand": "E.Leclerc Jardi"}, Categories.SHOP_GARDEN_CENTRE),
        "Hyper": ({"brand": "E.Leclerc"}, Categories.SHOP_SUPERMARKET),
        "Super": ({"brand": "E.Leclerc"}, Categories.SHOP_SUPERMARKET),
        "Manège à Bijoux": ({"brand": "Manège à Bijoux"}, Categories.SHOP_JEWELRY),
        "Drive": ({"brand": "E.Leclerc Drive"}, Categories.SHOP_OUTPOST),
        "Une Heure Pour Soi": ({"brand": "Une Heure Pour Soi"}, Categories.SHOP_PERFUMERY),
        "Station Service": ({"brand": "E.Leclerc"}, Categories.FUEL_STATION),
        "Auto": ({"brand": "E.Leclerc"}, Categories.SHOP_CAR_REPAIR),
        "E.Leclerc Express": ({"brand": "E.Leclerc Express"}, Categories.SHOP_SUPERMARKET),
        "Voyages": ({"brand": "E.Leclerc"}, Categories.SHOP_TRAVEL_AGENCY),
        "Espace Culturel": ({"brand": "E.Leclerc Espace Culturel"}, Categories.SHOP_ELECTRONICS),
        "Parapharmacie": ({"brand": " E.Leclerc Parapharmacie"}, Categories.PHARMACY),
        "Location": ({"brand": "E.Leclerc Location"}, Categories.CAR_RENTAL),
        "Brico": ({"brand": "E.Leclerc Brico"}, Categories.SHOP_DOITYOURSELF),
        "Click and Collect": None,
    }

    def parse_item(self, item, feature, **kwargs):
        if feature["properties"]["user_properties"]["type"] != "pdv":
            return None

        item["website"] = feature["properties"]["user_properties"].get("urlStore")
        item["facebook"] = feature["properties"]["user_properties"].get("catchmentArea", {}).get("urlFacebook")

        store_type = feature["properties"]["user_properties"]["commercialActivity"]["label"]
        if brand := self.brands.get(store_type):
            item.update(brand[0])
            if len(brand) == 2:
                apply_category(brand[1], item)
        else:
            self.crawler.stats.inc_value(
                f'atp/e_leclerc/unmapped_category/{store_type}/{feature["properties"]["user_properties"]["commercialActivity"]["activityCode"]}'
            )
            return None

        yield item
