from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.storefinders.geo_me import GeoMeSpider


class BPSpider(GeoMeSpider):
    name = "bp"
    key = "bpretaillocator"
    brands = {
        "BP": ("BP", "Q152057"),
        "AM": ("Amoco", "Q465952"),
        "ARAL Tankstelle": ("Aral", "Q565734"),
    }

    def parse_item(self, item, location):
        item["brand"], item["brand_wikidata"] = self.brands.get(location["site_brand"], self.brands["BP"])
        products = location["products"]
        facilities = location["facilities"]
        apply_category(Categories.FUEL_STATION, item)
        if "shop" in facilities:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        apply_yes_no("amenity:chargingstation", item, "electricity" in products)
        apply_yes_no("amenity:toilets", item, "toilet" in facilities)
        apply_yes_no("atm", item, "cash_point" in facilities)
        apply_yes_no("car_wash", item, "car_wash" in facilities)
        apply_yes_no("hgv", item, any("truck" in f for f in facilities))
        apply_yes_no("wheelchair", item, "disabled_facilities" in facilities)
        apply_yes_no(Fuel.ADBLUE, item, any("ad_blue" in p for p in products))
        apply_yes_no(Fuel.DIESEL, item, any("diesel" in p for p in products))
        apply_yes_no(Fuel.COLD_WEATHER_DIESEL, item, "diesel_frost" in products)
        apply_yes_no(Fuel.E10, item, "e10" in products)
        apply_yes_no(Fuel.E5, item, "euro_95" in products or "super_e5" in products)
        apply_yes_no(Fuel.GTL_DIESEL, item, any("ultimate_diesel" in p for p in products))
        apply_yes_no(Fuel.HGV_DIESEL, item, "truck_diesel" in products)
        apply_yes_no(Fuel.LPG, item, "lpg" in products)
        apply_yes_no(Fuel.OCTANE_100, item, any("100" in p for p in products))
        apply_yes_no(Fuel.OCTANE_91, item, any("premium_unlead" in p for p in products))
        apply_yes_no(Fuel.OCTANE_92, item, any("92" in p for p in products))
        apply_yes_no(Fuel.OCTANE_93, item, any("93" in p for p in products))
        apply_yes_no(Fuel.OCTANE_95, item, "unlead" in products or any("unleaded_95" in p for p in products))
        apply_yes_no(Fuel.OCTANE_98, item, "ultimate_unleaded" in products or any("98" in p for p in products))
        apply_yes_no(Fuel.UNTAXED_DIESEL, item, "red_diesel" in products)
        yield item
