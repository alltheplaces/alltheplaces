from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.storefinders.geo_me import GeoMeSpider


class ShellSpider(GeoMeSpider):
    name = "shell"
    item_attributes = {"brand": "Shell", "brand_wikidata": "Q110716465"}
    key = "shellgsllocator"

    def parse_item(self, item, location):
        # Definitions extracted from https://shellgsllocator.geoapp.me/config/published/retail/prod/en_US.json?format=json
        amenities = location["amenities"]
        fuels = location["fuels"]
        apply_category(Categories.FUEL_STATION, item)
        if "shop" in amenities:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        apply_yes_no("amenity:chargingstation", item, "electric_charging_other" in fuels or "shell_recharge" in fuels)
        apply_yes_no("toilets", item, "toilet" in amenities)
        apply_yes_no("atm", item, "atm" in amenities)
        apply_yes_no("car_wash", item, "carwash" in amenities)
        apply_yes_no("hgv", item, "hgv_lane" in amenities)
        apply_yes_no("wheelchair", item, "disabled_facilities" in amenities)
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
        yield item
