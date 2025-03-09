from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.mapdata_services import MapDataServicesSpider


class ReddyExpressAUSpider(MapDataServicesSpider):
    name = "reddy_express_au"
    item_attributes = {"operator": "Reddy Express", "operator_wikidata": "Q5144653"}
    api_brand_name = "SHE_FuelLocations"
    api_key = "KYAmqfaKFEsYWtweMcoqStasRlCoipBukIAt3gSb"
    api_filter = '(shell_card_accepted = 1) AND (Status = "Temp Closure" OR Status = "Open")'

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("uuid")
        item["street_address"] = item.pop("street", None)
        item["branch"] = item.pop("name", None)
        if not item["branch"].startswith("Shell Reddy Express "):
            return
        else:
            item["branch"] = item["branch"].removeprefix("Shell Reddy Express").strip()

        item["opening_hours"] = OpeningHours()
        if feature.get("open_24_hours") == "1":
            item["opening_hours"].add_days_range(DAYS, "00:00", "24:00")
        for day_abbrev in ["mon", "tues", "wed", "thurs", "fri", "sat", "sun"]:
            day_code = day_abbrev[0:3].title()
            open_time = feature.get(f"{day_code}_opening")
            close_time = feature.get(f"{day_code}_closing")
            item["opening_hours"].add_range(day_code, open_time, close_time)

        apply_category(Categories.FUEL_STATION, item)
        if feature.get("retail_shop") == "1":
            apply_category(Categories.SHOP_CONVENIENCE, item)
        if feature.get("restaurant") == "1":
            apply_category(Categories.RESTAURANT, item)
        apply_yes_no(Fuel.E10, item, feature.get("unleaded_e10") == "1", False)
        apply_yes_no(Fuel.OCTANE_91, item, feature.get("unleaded_91") == "1" or feature.get("unleaded_91_la") == "1", False)
        apply_yes_no(Fuel.OCTANE_95, item, feature.get("unleaded_95") == "1", False)
        apply_yes_no(Fuel.OCTANE_98, item, feature.get("unleaded_98") == "1" or feature.get("shell_v_power") == "1", False)
        apply_yes_no(Fuel.DIESEL, item, feature.get("diesel") == "1" or feature.get("premium_diesel") == "1" or feature.get("shell_v_power_diesel") == "1", False)
        apply_yes_no(Fuel.HGV_DIESEL, item, feature.get("high_flow_diesel") == "1" or "ultra_high_flow_diesel" == "1", False)
        apply_yes_no(Fuel.LPG, item, feature.get("autogas") == "1", False)
        apply_yes_no(Fuel.ADBLUE, item, feature.get("adblue_at_pump") == "1" or feature.get("adblue_by_pack") == "1", False)
        apply_yes_no(FuelCards.SHELL, item, feature.get("shell_card_accepted") == "1" or feature.get("shell_card_mobile_app_accepted") == "1", False)
        apply_yes_no(Extras.CAR_WASH, item, feature.get("carwash") == "1", False)
        apply_yes_no(Extras.TOILETS, item, feature.get("toilets") == "1", False)
        apply_yes_no(Extras.SHOWERS, item, feature.get("showers") == "1", False)
        apply_yes_no(Extras.ATM, item, feature.get("atm") == "1", False)
        apply_yes_no(Extras.INDOOR_SEATING, item, feature.get("truckers_lounge") == "1", False)
        apply_yes_no(Extras.FAST_FOOD, item, feature.get("takeaway_food") == "1", False)

        yield item
