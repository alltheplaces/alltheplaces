from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.caseys_general_store import CaseysGeneralStoreSpider
from locations.spiders.chevron_us import ChevronUSSpider
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.costco import CostcoSpider
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.dunkin_us import DunkinUSSpider
from locations.spiders.food_city_us import FoodCityUSSpider
from locations.spiders.giant_food import GiantFoodSpider
from locations.spiders.giant_food_stores import GiantFoodStoresSpider
from locations.spiders.godfathers_pizza import GodfathersPizzaSpider
from locations.spiders.h_e_b_us import HEBUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.marcs import MarcsSpider
from locations.spiders.market_basket import MarketBasketSpider
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.spiders.nordstrom import NordstromSpider
from locations.spiders.piggly_wiggly_us import PigglyWigglyUSSpider
from locations.spiders.race_trac_us import RaceTracUSSpider
from locations.spiders.recipe_unlimited import RecipeUnlimitedSpider
from locations.spiders.rite_aid_us import RiteAidUSSpider
from locations.spiders.royal_farms import RoyalFarmsSpider
from locations.spiders.safeway import SafewaySpider
from locations.spiders.schnucks_us import SchnucksUSSpider
from locations.spiders.seven_eleven_ca_us import SevenElevenCAUSSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite import ShopriteSpider
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.thrifty_foods_ca import ThriftyFoodsCASpider
from locations.spiders.united_dairy_farmers_us import UnitedDairyFarmersUSSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.wawa import WawaSpider
from locations.spiders.wegmans import WegmansSpider
from locations.storefinders.where2getit import Where2GetItSpider


class BmoSpider(Where2GetItSpider):
    name = "bmo"
    item_attributes = {"brand": "BMO", "brand_wikidata": "Q4835981"}
    api_endpoint = "https://branchlocator.bmo.com/rest/getlist"
    api_key = "343095D0-C235-11E6-93AB-1BF70C70A832"
    api_filter_admin_level = 2

    # flake8: noqa: C901
    def parse_item(self, item: Feature, location: dict):
        item["ref"] = location["clientkey"]
        item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
        if location["country"] == "CA":
            item["state"] = location["province"]

        hours_text = ""
        for day_name in DAYS_FULL:
            open_time = location.get("{}open".format(day_name.lower()))
            close_time = location.get("{}close".format(day_name.lower()))
            if (
                open_time
                and open_time != "closed"
                and open_time != "N/A"
                and close_time
                and close_time != "closed"
                and close_time != "N/A"
            ):
                hours_text = "{} {}: {} - {}".format(hours_text, day_name, open_time, close_time)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)

        if location["grouptype"] in ["BMOHarrisBranches", "BMOBranches"]:
            apply_category(Categories.BANK, item)
            if location.get("abmcount"):
                apply_yes_no(Extras.ATM, item, True, False)
        elif location["grouptype"] in ["BMOHarrisATM", "BMOATM"]:
            apply_category(Categories.ATM, item)
            if item["name"] == "Alon 7-Eleven":
                item["located_in"] = SevenElevenCAUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SevenElevenCAUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Arco":
                item["located_in"] = MarathonPetroleumUSSpider.brands["ARCO"]["brand"]
                item["located_in_wikidata"] = MarathonPetroleumUSSpider.brands["ARCO"]["brand_wikidata"]
            elif item["name"] == "Casey's":
                item["located_in"] = CaseysGeneralStoreSpider.item_attributes["brand"]
                item["located_in_wikidata"] = CaseysGeneralStoreSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Chevron":
                item["located_in"] = ChevronUSSpider.CHEVRON["brand"]
                item["located_in_wikidata"] = ChevronUSSpider.CHEVRON["brand_wikidata"]
            elif item["name"] == "Circle K" or item["name"] == "Irving - Circle K":
                item["located_in"] = CircleKSpider.CIRCLE_K["brand"]
                item["located_in_wikidata"] = CircleKSpider.CIRCLE_K["brand_wikidata"]
            elif item["name"] == "City Market":
                item["located_in"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand_wikidata"]
            elif item["name"] == "Costco":
                item["located_in"] = CostcoSpider.item_attributes["brand"]
                item["located_in_wikidata"] = CostcoSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "CVS":
                item["located_in"] = CVS_BRANDS["CVS Pharmacy"]["brand"]
                item["located_in_wikidata"] = CVS_BRANDS["CVS Pharmacy"]["brand_wikidata"]
            elif item["name"] == "Dillons":
                item["located_in"] = KROGER_BRANDS["https://www.dillons.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.dillons.com/"]["brand_wikidata"]
            elif item["name"] == "Duane Reade":
                item["located_in"] = WalgreensSpider.DUANE_READE["brand"]
                item["located_in_wikidata"] = WalgreensSpider.DUANE_READE["brand_wikidata"]
            elif item["name"] == "Dunkin Donuts":
                item["located_in"] = DunkinUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = DunkinUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Food 4 Less":
                item["located_in"] = KROGER_BRANDS["https://www.food4less.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.food4less.com/"]["brand_wikidata"]
            elif item["name"] == "Food City":
                item["located_in"] = FoodCityUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = FoodCityUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Fred Meyer":
                item["located_in"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand_wikidata"]
            elif item["name"] == "Fry's":
                item["located_in"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand_wikidata"]
            elif item["name"] == "Giant Food":
                item["located_in"] = GiantFoodSpider.item_attributes["brand"]
                item["located_in_wikidata"] = GiantFoodSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Giant Food Store" or item["name"] == "Giant Food Stores":
                item["located_in"] = GiantFoodStoresSpider.item_attributes["brand"]
                item["located_in_wikidata"] = GiantFoodStoresSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Godfathers Pizza":
                item["located_in"] = GodfathersPizzaSpider.item_attributes["brand"]
                item["located_in_wikidata"] = GodfathersPizzaSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Harris Teeter":
                item["located_in"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand_wikidata"]
            elif item["name"] == "Harveys":
                item["located_in"] = RecipeUnlimitedSpider.brands["Harvey's"]["brand"]
                item["located_in_wikidata"] = RecipeUnlimitedSpider.brands["Harvey's"]["brand_wikidata"]
            elif item["name"] == "Heb":
                item["located_in"] = HEBUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = HEBUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Kroger" or item["name"] == "Kroger Fuel Center":
                item["located_in"] = KROGER_BRANDS["https://www.kroger.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.kroger.com/"]["brand_wikidata"]
            elif item["name"] == "Longs Drugs":
                item["located_in"] = CVS_BRANDS["Longs Drugs"]["brand"]
                item["located_in_wikidata"] = CVS_BRANDS["Longs Drugs"]["brand_wikidata"]
            elif item["name"] == "Marcs":
                item["located_in"] = MarcsSpider.item_attributes["brand"]
                item["located_in_wikidata"] = MarcsSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Market Basket":
                item["located_in"] = MarketBasketSpider.item_attributes["brand"]
                item["located_in_wikidata"] = MarketBasketSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Mcdonalds":
                item["located_in"] = McdonaldsSpider.item_attributes["brand"]
                item["located_in_wikidata"] = McdonaldsSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Nordstrom":
                item["located_in"] = NordstromSpider.item_attributes["brand"]
                item["located_in_wikidata"] = NordstromSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Piggly Wiggly":
                item["located_in"] = PigglyWigglyUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = PigglyWigglyUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Qfc" or item["name"] == "Quality Food Center":
                item["located_in"] = KROGER_BRANDS["https://www.qfc.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.qfc.com/"]["brand_wikidata"]
            elif item["name"] == "Racetrac" or item["name"].startswith("Racetrac "):
                item["located_in"] = RaceTracUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RaceTracUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Ralphs":
                item["located_in"] = KROGER_BRANDS["https://www.ralphs.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.ralphs.com/"]["brand_wikidata"]
            elif item["name"] == "Royal Farms" or item["name"].startswith("Royal Farms "):
                item["located_in"] = RoyalFarmsSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RoyalFarmsSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Rite Aid":
                item["located_in"] = RiteAidUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RiteAidUSSpider.item_attributes["brand_wikidata"]
            elif item["name"].startswith("SAFEWAY "):
                item["located_in"] = SafewaySpider.item_attributes["brand"]
                item["located_in_wikidata"] = SafewaySpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Schnucks":
                item["located_in"] = SchnucksUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SchnucksUSSpider.item_attributes["brand_wikidata"]
            elif (
                item["name"] == "Shell"
                or item["name"].upper().startswith("SHELL C")
                or item["name"].upper().startswith("SHELL #")
            ):
                item["located_in"] = ShellSpider.item_attributes["brand"]
                item["located_in_wikidata"] = ShellSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Shoprite" or item["name"] == "Shop Rite":
                item["located_in"] = ShopriteSpider.item_attributes["brand"]
                item["located_in_wikidata"] = ShopriteSpider.item_attributes["brand_wikidata"]
            elif (
                item["name"] == "Smiths Food and Drugs"
                or item["name"] == "Smiths"
                or item["name"] == "Smith's"
                or item["name"] == "Smiths Fuel Center"
            ):
                item["located_in"] = KROGER_BRANDS["https://www.smithsfoodanddrug.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.smithsfoodanddrug.com/"]["brand_wikidata"]
            elif item["name"].startswith("Speedway "):
                item["located_in"] = SpeedwayUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SpeedwayUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Sunoco" or item["name"].startswith("Sunoco "):
                item["located_in"] = SunocoUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SunocoUSSpider.item_attributes["brand_wikidata"]
            elif item["name"].startswith("THRIFTY FOODS "):
                item["located_in"] = ThriftyFoodsCASpider.item_attributes["brand"]
                item["located_in_wikidata"] = ThriftyFoodsCASpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Tom Thumb":
                item["located_in"] = AlbertsonsSpider.brands["tomthumb"]["brand"]
                item["located_in_wikidata"] = AlbertsonsSpider.brands["tomthumb"]["brand_wikidata"]
            elif item["name"] == "United Dairy Farmers":
                item["located_in"] = UnitedDairyFarmersUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = UnitedDairyFarmersUSSpider.item_attributes["brand_wikidata"]
            elif item["name"].upper().startswith("WALGREENS "):
                item["located_in"] = WalgreensSpider.WALGREENS["brand"]
                item["located_in_wikidata"] = WalgreensSpider.WALGREENS["brand_wikidata"]
            elif item["name"] == "Wawa" or item["name"].startswith("Wawa "):
                item["located_in"] = WawaSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WawaSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Wegmans" or item["name"] == "Wegmans Food Market":
                item["located_in"] = WegmansSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WegmansSpider.item_attributes["brand_wikidata"]
        else:
            self.logger.error("Unknown location type: %s", location["grouptype"])

        yield item
