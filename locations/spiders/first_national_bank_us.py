from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.spiders.eatn_park_us import EatnParkUSSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.food_lion_us import FoodLionUSSpider
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.giant_food_us import GiantFoodUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.royal_farms import RoyalFarmsSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.walmart_us import WalmartUSSpider
from locations.storefinders.yext_answers import YextAnswersSpider


class FirstNationalBankUSSpider(YextAnswersSpider):
    name = "first_national_bank_us"
    item_attributes = {"brand": "First National Bank", "brand_wikidata": "Q5426765"}
    api_key = "10f82fdf7a37ee369b154241c59dade1"
    experience_key = "fnb-answers"

    LOCATED_IN_MAPPINGS = [
        (["GIANT FOOD", "GIANT"], GiantFoodUSSpider.item_attributes),
        (["FOOD LION"], FoodLionUSSpider.item_attributes),
        (["WALMART", "WAL-MART", "WAL MART"], WalmartUSSpider.item_attributes),
        (["EXXON"], ExxonMobilSpider.brands["Exxon"]),
        (["SUNOCO"], SunocoUSSpider.item_attributes),
        (["MARATHON"], MarathonPetroleumUSSpider.brands["MARATHON"]),
        (["HARRIS TEETER"], KROGER_BRANDS["https://www.harristeeter.com/"]),
        (["ROYAL FARMS"], RoyalFarmsSpider.item_attributes),
        (["SPINX"], {"brand": "Spinx", "brand_wikidata": "Q121851498"}),
        (["GETGO"], GiantEagleUSSpider.GET_GO),
        (["REFUEL"], {"brand": "Refuel", "brand_wikidata": "Q124987140"}),
        (["EAT N PARK"], EatnParkUSSpider.item_attributes),
    ]

    def parse_item(self, location, item):
        if location["type"] == "atm":
            apply_category(Categories.ATM, item)
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item.get("branch", ""), self.LOCATED_IN_MAPPINGS, self
            )
        elif location["type"] == "location":
            apply_category(Categories.BANK, item)
            if amenities := location.get("c_branchFilters"):
                apply_yes_no(Extras.ATM, item, "ATM" in amenities, False)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in amenities, False)
        else:
            self.logger.error("Unknown location type: {}".format(location["type"]))
        yield item
