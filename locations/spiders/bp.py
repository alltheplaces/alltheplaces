from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
)
from locations.hours import DAYS, OpeningHours
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

        if "bp_connect_store" in facilities:
            bp_connect_item = item.deepcopy()
            bp_connect_item["ref"] = item.get("ref") + "-attachecd-bp-connect-shop"
            bp_connect_item["name"] = "BP Connect"
            bp_connect_item["brand"] = "BP Connect"
            bp_connect_item["brand_wikidata"] = "Q152057"
            if "shop_open_24_hours" in facilities:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            apply_category(Categories.SHOP_CONVENIENCE, bp_connect_item)
            yield bp_connect_item

        apply_category(Categories.FUEL_STATION, item)
        if "shop" in facilities:
            apply_yes_no("shop", item, True)
        if "restaurant" in facilities:
            apply_yes_no("food", item, True)

        if "electric_charging" in facilities or "electricity" in products:
            apply_yes_no("fuel:electricity", item, True)

        apply_yes_no(Extras.TOILETS, item, any("toilet" in a for a in facilities))
        apply_yes_no(Extras.SHOWERS, item, "shower" in facilities)
        apply_yes_no(Extras.ATM, item, "cash_point" in facilities)
        apply_yes_no(
            Extras.CAR_WASH,
            item,
            "car_wash" in facilities or "car_wash_self_service" in facilities or "super_wash" in facilities,
        )
        apply_yes_no(Extras.VACUUM_CLEANER, item, "vacuum_cleaner" in facilities)
        apply_yes_no(Extras.WIFI, item, "wifi" in facilities)
        apply_yes_no(Access.HGV, item, any("truck" in f for f in facilities))
        apply_yes_no(Extras.WHEELCHAIR, item, "disabled_facilities" in facilities)
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
        apply_yes_no(PaymentMethods.VISA, item, "visa" in facilities)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in facilities)
        apply_yes_no(FuelCards.BP, item, "bp_fuel_card" in facilities or "euroshell_card" in facilities)
        apply_yes_no(FuelCards.DKV, item, "dkv" in facilities)
        apply_yes_no(FuelCards.UTA, item, "uta" in facilities)
        yield item
