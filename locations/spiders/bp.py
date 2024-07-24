from typing import Iterable

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
from locations.items import Feature
from locations.storefinders.geo_me import GeoMeSpider


class BpSpider(GeoMeSpider):
    name = "bp"
    key = "bpretaillocator"
    brands = {
        "bp": {"brand": "BP", "brand_wikidata": "Q152057"},
        "aral": {"brand": "Aral", "brand_wikidata": "Q565734"},
        "amoco": {"brand": "Amoco", "brand_wikidata": "Q465952"},
        "aral_pulse": {"brand": "Aral pulse", "operator": "Aral", "operator_wikidata": "Q565734"},
    }

    def parse_item(self, item, location):
        if brand := self.brands.get(location["site_brand"]):
            item.update(brand)
        else:
            item.update(self.brands["BP"])
            self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, location["site_brand"]))

        products = location["products"]
        facilities = location["facilities"]

        yield from self.parse_stores(item, location) or []

        if location["site_brand"] == "aral_pulse":
            item["located_in"] = item.pop("name")
            apply_category(Categories.CHARGING_STATION, item)
        else:
            apply_category(Categories.FUEL_STATION, item)

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

    store_brands = {
        "bp_connect_store": {"name": "BP Connect", "brand": "BP Connect", "brand_wikidata": "Q152057"},
        "aral_store": {"name": "Aral", "brand": "Aral", "brand_wikidata": "Q565734"},
        "rewe_to_go": {"name": "REWE To Go", "brand": "REWE To Go", "brand_wikidata": "Q85224313"},
        "wild_bean_cafe": {"name": "Wild Bean Cafe", "brand": "Wild Bean Cafe", "brand_wikidata": "Q61804826"},
    }

    def parse_stores(self, item: Feature, location: dict) -> Iterable[Feature]:
        for store_key in self.store_brands.keys():
            if store_key not in location["facilities"]:
                continue
            store = item.deepcopy()
            store["ref"] = "{}-{}".format(item.get("ref"), store_key)
            store.update(self.store_brands[store_key])

            store["opening_hours"] = "24/7" if "shop_open_24_hours" in location["facilities"] else None

            if store_key == "wild_bean_cafe":
                apply_category(Categories.CAFE, store)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, store)
            yield store
