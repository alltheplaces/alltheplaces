from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.spiders.otr_au import OtrAUSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.vets4pets_gb import set_located_in
from locations.storefinders.mapdata_services import MapDataServicesSpider

SHOP_BRANDS = {
    "Reddy Express": {"brand": "Reddy Express", "brand_wikidata": "Q5144653"},
    "Coles Express": {},
    "Otr": OtrAUSpider.item_attributes,
}
FUEL_BRANDS = {
    "Advantage": None,
    "Ampol": None,
    "BP": None,
    "Caltex": None,
    "Liberty": None,
    "Shell": ShellSpider.item_attributes,
    "TPSC": None,
    "Westside": None,
}


class ShellAUSpider(MapDataServicesSpider):
    name = "shell_au"
    api_brand_name = "SHE_FuelLocations"
    api_key = "KYAmqfaKFEsYWtweMcoqStasRlCoipBukIAt3gSb"
    api_filter = '(shell_card_accepted = 1) AND (Status = "Temp Closure" OR Status = "Open")'

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not FUEL_BRANDS.get(feature["forecourt_brand"]):
            return

        item["ref"] = feature.get("uuid")
        item["street_address"] = item.pop("street", None)

        if feature.get("retail_shop") == "1":
            shop = item.deepcopy()
            shop["ref"] = "{}-shop".format(shop["ref"])
            set_located_in(shop, FUEL_BRANDS[feature["forecourt_brand"]])

            apply_category(Categories.SHOP_CONVENIENCE, shop)

            name = shop.pop("name").removeprefix(feature["forecourt_brand"]).strip()
            for shop_brand in SHOP_BRANDS.keys():
                if name.startswith(shop_brand):
                    shop["branch"] = name.removeprefix(shop_brand).strip()
                    shop.update(SHOP_BRANDS[shop_brand])
                    break

            yield shop

        item.update(FUEL_BRANDS[feature["forecourt_brand"]])
        apply_category(Categories.FUEL_STATION, item)

        item["opening_hours"] = OpeningHours()
        if feature.get("open_24_hours") == "1":
            item["opening_hours"] = "24/7"
        else:
            for day in DAYS_3_LETTERS:
                item["opening_hours"].add_range(
                    day, feature.get("{}_opening".format(day)), feature.get("{}_closing".format(day))
                )

        apply_yes_no(Fuel.E10, item, feature.get("unleaded_e10") == "1", "unleaded_e10" not in feature)
        apply_yes_no(Fuel.OCTANE_91, item, feature.get("unleaded_91") == "1" or feature.get("unleaded_91_la") == "1")
        apply_yes_no(Fuel.OCTANE_95, item, feature.get("unleaded_95") == "1", "unleaded_95" not in feature)
        apply_yes_no(Fuel.OCTANE_98, item, feature.get("unleaded_98") == "1" or feature.get("shell_v_power") == "1")
        apply_yes_no(
            Fuel.DIESEL,
            item,
            feature.get("diesel") == "1"
            or feature.get("premium_diesel") == "1"
            or feature.get("shell_v_power_diesel") == "1",
        )
        apply_yes_no(Fuel.HGV_DIESEL, item, feature.get("high_flow_diesel") == "1" or "ultra_high_flow_diesel" == "1")
        apply_yes_no(Fuel.LPG, item, feature.get("autogas") == "1", "autogas" not in feature)
        apply_yes_no(Fuel.ADBLUE, item, feature.get("adblue_at_pump") == "1" or feature.get("adblue_by_pack") == "1")
        apply_yes_no(
            FuelCards.SHELL,
            item,
            feature.get("shell_card_accepted") == "1" or feature.get("shell_card_mobile_app_accepted") == "1",
        )
        apply_yes_no(Extras.CAR_WASH, item, feature.get("carwash") == "1", "carwash" not in feature)
        apply_yes_no(Extras.TOILETS, item, feature.get("toilets") == "1", "toilets" not in feature)
        apply_yes_no(Extras.SHOWERS, item, feature.get("showers") == "1", "showers" not in feature)
        apply_yes_no(Extras.ATM, item, feature.get("atm") == "1", "atm" in feature)
        apply_yes_no(Extras.FAST_FOOD, item, feature.get("takeaway_food") == "1", "takeaway_food" not in feature)

        yield item
