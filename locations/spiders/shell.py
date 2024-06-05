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


class ShellSpider(GeoMeSpider):
    name = "shell"
    item_attributes = {"brand": "Shell", "brand_wikidata": "Q110716465"}
    key = "shellgsllocator"

    def parse_item(self, item, location):
        # Definitions extracted from https://shellgsllocator.geoapp.me/config/published/retail/prod/en_US.json?format=json
        amenities = location["amenities"]
        fuels = location["fuels"]

        # As we know the name of the shop attached we create its own POI
        if "selectshop" in amenities:
            select_shop_item = item.deepcopy()
            select_shop_item["ref"] = item.get("ref") + "-attached-shop"
            select_shop_item["name"] = "Shell Select"
            select_shop_item["brand"] = "Shell Select"
            select_shop_item["brand_wikidata"] = "Q124359752"
            apply_category(Categories.SHOP_CONVENIENCE, select_shop_item)
            yield select_shop_item

        apply_category(Categories.FUEL_STATION, item)

        # As we do not know the name of shop/restaurant attached, we apply to main item
        if "shop" in amenities:
            apply_yes_no("shop", item, True)
        if "restaurant" in amenities:
            apply_yes_no("food", item, True)

        if "twenty_four_hour" in amenities:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        if "charging" in amenities or "electric_charging_other" in fuels or "shell_recharge" in fuels:
            apply_yes_no("fuel:electricity", item, True)

        apply_yes_no(Extras.TOILETS, item, any("toilet" in a for a in amenities))
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "wheelchair_accessible_toilet" in amenities)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "baby_change_facilities" in amenities)
        apply_yes_no(Extras.SHOWERS, item, "shower" in amenities)
        apply_yes_no(Extras.ATM, item, "atm" in amenities or "atm_in" in amenities or "atm_out" in amenities)
        apply_yes_no(
            Extras.CAR_WASH, item, any("carwash" in a for a in amenities) or any("car_wash" in a for a in amenities)
        )
        apply_yes_no(Extras.WHEELCHAIR, item, "disabled_facilities" in amenities)
        apply_yes_no(Extras.COMPRESSED_AIR, item, "air_and_water" in amenities)
        apply_yes_no(Extras.VACUUM_CLEANER, item, "vacuum" in amenities)
        apply_yes_no(Extras.WIFI, item, "wifi" in amenities)
        apply_yes_no(Access.HGV, item, "hgv_lane" in amenities)
        apply_yes_no(Fuel.DIESEL, item, any("diesel" in f for f in fuels))
        apply_yes_no(Fuel.ADBLUE, item, any("adblue" in a for a in amenities))
        apply_yes_no(Fuel.BIODIESEL, item, "biodiesel" in fuels or "biofuel_gasoline" in fuels)
        apply_yes_no(Fuel.CNG, item, "cng" in fuels)
        apply_yes_no(Fuel.GTL_DIESEL, item, "gtl" in fuels)
        apply_yes_no(Fuel.HGV_DIESEL, item, "truck_diesel" in fuels or "hgv_lane" in amenities)
        apply_yes_no(Fuel.PROPANE, item, "auto_rv_propane" in fuels)
        apply_yes_no(Fuel.LH2, item, "hydrogen" in fuels)
        apply_yes_no(Fuel.LNG, item, "lng" in fuels)
        apply_yes_no(Fuel.LPG, item, "autogas_lpg" in fuels)
        # Definition of low-octane varies by country; 92 is most common
        apply_yes_no(Fuel.OCTANE_92, item, "low_octane_gasoline" in fuels)
        # Definition of mid-octane varies by country; 95 is most common
        apply_yes_no(Fuel.OCTANE_95, item, any("midgrade_gasoline" in f for f in fuels) or "unleaded_super" in fuels)
        # The US region seems to also use 'premium_gasoline' to refer to non-diesel gas products
        apply_yes_no(Fuel.OCTANE_98, item, any("98" in f for f in fuels) or "premium_gasoline" in fuels)
        apply_yes_no(Fuel.OCTANE_100, item, "super_premium_gasoline" in fuels)
        apply_yes_no(Fuel.ENGINE_OIL, item, "oil_and_lubricants" in amenities)
        apply_yes_no(PaymentMethods.VISA, item, "credit_card_visa" in amenities)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "credit_card_mastercard" in amenities)
        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "credit_card_american_express" in amenities)
        apply_yes_no(PaymentMethods.DINERS_CLUB, item, "credit_card_diners_club" in amenities)
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "apple_pay" in amenities)
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "google_pay" in amenities)
        apply_yes_no(FuelCards.SHELL, item, "shell_card" in amenities or "euroshell_card" in amenities)
        apply_yes_no(FuelCards.DKV, item, "fleet_card_dkv" in amenities)
        apply_yes_no(FuelCards.ESSO_NATIONAL, item, "fleet_card_esso" in amenities)
        apply_yes_no(FuelCards.UTA, item, "fleet_card_uta" in amenities)
        yield item
