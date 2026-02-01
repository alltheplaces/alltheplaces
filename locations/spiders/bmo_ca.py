from typing import Iterable

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.ampm_us import AmpmUSSpider
from locations.spiders.bashas_us import BashasUSSpider
from locations.spiders.brookshires_us import BrookshiresUSSpider
from locations.spiders.cardenas_us import CardenasUSSpider
from locations.spiders.caseys_general_store import CaseysGeneralStoreSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.costco_ca_gb_us import CostcoCAGBUSSpider
from locations.spiders.cvs_us import CVS
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.dunkin_us import DunkinUSSpider
from locations.spiders.eg_america_us import EgAmericaUSSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.food_city_southeast_us import FoodCitySoutheastUSSpider
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.giant_food_stores import GiantFoodStoresSpider
from locations.spiders.giant_food_us import GiantFoodUSSpider
from locations.spiders.godfathers_pizza import GodfathersPizzaSpider
from locations.spiders.h_e_b_us import HEBUSSpider
from locations.spiders.haggen import HaggenSpider
from locations.spiders.iga import IgaSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.mapco_us import MapcoUSSpider
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.marcs import MarcsSpider
from locations.spiders.market_basket_us import MarketBasketUSSpider
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.spiders.nordstrom import NordstromSpider
from locations.spiders.piggly_wiggly_us import PigglyWigglyUSSpider
from locations.spiders.quickchek_us import QuickchekUSSpider
from locations.spiders.race_trac_us import RaceTracUSSpider
from locations.spiders.recipe_unlimited import RecipeUnlimitedSpider
from locations.spiders.rite_aid_us import RiteAidUSSpider
from locations.spiders.royal_farms import RoyalFarmsSpider
from locations.spiders.safeway import SafewaySpider
from locations.spiders.schnucks_us import SchnucksUSSpider
from locations.spiders.seven_eleven_ca_us import SevenElevenCAUSSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_us import ShopriteUSSpider
from locations.spiders.sobeys_ca import SobeysCASpider
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.speedy_stop_us import SpeedyStopUSSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.texaco_co import TEXACO_SHARED_ATTRIBUTES
from locations.spiders.thrifty_foods_ca import ThriftyFoodsCASpider
from locations.spiders.united_dairy_farmers_us import UnitedDairyFarmersUSSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.wawa import WawaSpider
from locations.spiders.wegmans_us import WegmansUSSpider
from locations.spiders.winn_dixie_us import WinnDixieUSSpider
from locations.storefinders.where2getit import Where2GetItSpider

LOCATION_MAPPINGS = [
    (["7-ELEVEN", "ALON 7-ELEVEN"], SevenElevenCAUSSpider.item_attributes),
    (["ACME", "ACME MARKETS"], AlbertsonsSpider.brands["acmemarkets"]),
    (["ALBERTSON'S", "ALBERTSONS"], AlbertsonsSpider.brands["albertsons"]),
    (["AMPM", "AM/PM", "AM PM"], AmpmUSSpider.item_attributes),
    (["APLUS", "A-PLUS", "A PLUS"], {"brand": "APlus", "brand_wikidata": "Q4646934"}),
    (["ARCO"], MarathonPetroleumUSSpider.brands["ARCO"]),
    (["BASHAS", "BASHAS'"], BashasUSSpider.item_attributes),
    (["BROOKSHIRES", "BROOKSHIRE'S"], BrookshiresUSSpider.item_attributes),
    (["CARDENAS", "CARDENAS MARKET"], CardenasUSSpider.item_attributes),
    (["CASEY'S", "CASEYS"], CaseysGeneralStoreSpider.item_attributes),
    (["CHEVRON"], CHEVRON_BRANDS["Chevron"][0]),
    (["CIRCLE K", "IRVING - CIRCLE K"], CircleKSpider.CIRCLE_K),
    (["CERTIFIED", "CERTIFIED OIL"], EgAmericaUSSpider.brands[17]),
    (["CITY MARKET"], KROGER_BRANDS["https://www.citymarket.com/"]),
    (["COSTCO"], CostcoCAGBUSSpider.item_attributes),
    (["CVS"], CVS),
    (["DARI MART"], {"brand": "Dari Mart", "brand_wikidata": "Q5222675"}),
    (["DILLONS"], KROGER_BRANDS["https://www.dillons.com/"]),
    (["DUANE READE"], WalgreensSpider.DUANE_READE),
    (["DUNKIN DONUTS", "DUNKIN'", "DUNKIN"], DunkinUSSpider.item_attributes),
    (["FAMILY EXPRESS"], {"brand": "Family Express", "brand_wikidata": "Q85760458"}),
    (["FOOD 4 LESS"], KROGER_BRANDS["https://www.food4less.com/"]),
    (["FOOD CITY"], FoodCitySoutheastUSSpider.item_attributes),
    (["FOODS CO"], KROGER_BRANDS["https://www.foodsco.net/"]),
    (["FRED MEYER"], KROGER_BRANDS["https://www.fredmeyer.com/"]),
    (["FRY'S", "FRYS"], KROGER_BRANDS["https://www.frysfood.com/"]),
    (["GETGO", "GET GO"], GiantEagleUSSpider.GET_GO),
    (["GIANT EAGLE"], GiantEagleUSSpider.GIANT_EAGLE),
    (["GIANT FOOD STORE", "GIANT FOOD STORES"], GiantFoodStoresSpider.item_attributes),
    (["GIANT FOOD"], GiantFoodUSSpider.item_attributes),
    (["GODFATHERS PIZZA", "GODFATHER'S PIZZA"], GodfathersPizzaSpider.item_attributes),
    (["HAGGEN"], HaggenSpider.item_attributes),
    (["HARRIS TEETER"], KROGER_BRANDS["https://www.harristeeter.com/"]),
    (["HOMELAND", "HOMELAND STORE"], {"brand": "Homeland", "brand_wikidata": "Q5889497"}),
    (["HUCKS", "HUCK'S"], {"brand": "Huck's Food & Fuel", "brand_wikidata": "Q56276328"}),
    (["HARVEYS", "HARVEY'S"], RecipeUnlimitedSpider.brands["Harvey's"]),
    (["HEB", "H-E-B"], HEBUSSpider.item_attributes),
    (["IGA"], IgaSpider.item_attributes),
    (["JEWEL OSCO", "JEWEL-OSCO"], AlbertsonsSpider.brands["jewelosco"]),
    (["KROGER"], KROGER_BRANDS["https://www.kroger.com/"]),
    (["KWIK SHOP", "KWIKSHOP"], EgAmericaUSSpider.brands[18]),
    (["LOAF 'N JUG", "LOAF N JUG", "LOAFNJUG"], EgAmericaUSSpider.brands[19]),
    (["LONGS DRUGS"], CVS_BRANDS["Longs Drugs"]),
    (["MAPCO"], MapcoUSSpider.item_attributes),
    (["MARCS", "MARC'S"], MarcsSpider.item_attributes),
    (["MARKET BASKET"], MarketBasketUSSpider.item_attributes),
    (["MCDONALDS", "MCDONALD'S"], McdonaldsSpider.item_attributes),
    (["MOBIL"], ExxonMobilSpider.brands["Mobil"]),
    (["NORDSTROM"], NordstromSpider.item_attributes),
    (["PIGGLY WIGGLY"], PigglyWigglyUSSpider.item_attributes),
    (["QFC", "QUALITY FOOD CENTER"], KROGER_BRANDS["https://www.qfc.com/"]),
    (["QUICKCHEK"], QuickchekUSSpider.item_attributes),
    (["QUIK STOP"], EgAmericaUSSpider.brands[11]),
    (["RACETRAC"], RaceTracUSSpider.item_attributes),
    (["RANDALLS"], AlbertsonsSpider.brands["randalls"]),
    (["RALPHS"], KROGER_BRANDS["https://www.ralphs.com/"]),
    (["ROYAL FARMS"], RoyalFarmsSpider.item_attributes),
    (["RITE AID"], RiteAidUSSpider.item_attributes),
    (["RUTTERS", "RUTTER'S"], {"brand": "Rutter's", "brand_wikidata": "Q7383544"}),
    (["SAFEWAY"], SafewaySpider.item_attributes),
    (["SHAWS", "SHAW'S"], AlbertsonsSpider.brands["shaws"]),
    (["SCHNUCKS"], SchnucksUSSpider.item_attributes),
    (["SHELL"], ShellSpider.item_attributes),
    (["SHOPRITE", "SHOP RITE"], ShopriteUSSpider.item_attributes),
    (["SOBEYS"], SobeysCASpider.item_attributes),
    (["SMITHS FOOD AND DRUGS", "SMITHS", "SMITH'S"], KROGER_BRANDS["https://www.smithsfoodanddrug.com/"]),
    (["SPEEDWAY"], SpeedwayUSSpider.item_attributes),
    (["SPEEDY STOP"], SpeedyStopUSSpider.item_attributes),
    (["SUNOCO"], SunocoUSSpider.item_attributes),
    (["TARGET"], TargetUSSpider.item_attributes),
    (["TEXACO"], TEXACO_SHARED_ATTRIBUTES),
    (["THRIFTY FOODS"], ThriftyFoodsCASpider.item_attributes),
    (["TOM THUMB", "TOM  THUMB"], AlbertsonsSpider.brands["tomthumb"]),
    (["UNITED DAIRY FARMERS", "UDF"], UnitedDairyFarmersUSSpider.item_attributes),
    (["UNITED SUPERMARKET", "UNITED SUPERMARKETS"], AlbertsonsSpider.brands["unitedsupermarkets"]),
    (["VONS"], AlbertsonsSpider.brands["vons"]),
    (["WALGREENS"], WalgreensSpider.WALGREENS),
    (["WAWA"], WawaSpider.item_attributes),
    (["WEGMANS"], WegmansUSSpider.item_attributes),
    (["WINN DIXIE", "WINN-DIXIE"], WinnDixieUSSpider.item_attributes),
]


class BmoCASpider(Where2GetItSpider):
    name = "bmo_ca"
    item_attributes = {"brand": "BMO", "brand_wikidata": "Q4835981"}
    api_brand_name = "bmobranch"
    api_key = "343095D0-C235-11E6-93AB-1BF70C70A832"
    api_filter_admin_level = 2

    # flake8: noqa: C901
    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item["ref"] = location["clientkey"]
        item["street_address"] = clean_address([location.get("address1"), location.get("address2")])

        if isinstance(location.get("links", None), list):
            # Sometimes multiple websites are listed in different locales.
            # English is observed to be the first in the list, so use that.
            item["website"] = location["links"][0]

        try:
            item["opening_hours"] = self.parse_opening_hours(location)
        except:
            self.logger.error("Failed to parse opening hours")

        if location["grouptype"].startswith("BMO") and location["grouptype"].endswith("Branches"):
            apply_category(Categories.BANK, item)
            if location.get("abmcount"):
                apply_yes_no(Extras.ATM, item, True, False)
        elif location["grouptype"].startswith("BMO") and location["grouptype"].endswith("ATM"):
            apply_category(Categories.ATM, item)
<<<<<<< HEAD:locations/spiders/bmo_ca.py
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
                item["located_in"] = CHEVRON_BRANDS["Chevron"][0]["brand"]
                item["located_in_wikidata"] = CHEVRON_BRANDS["Chevron"][0]["brand_wikidata"]
            elif item["name"] == "Circle K" or item["name"] == "Irving - Circle K":
                item["located_in"] = CircleKSpider.CIRCLE_K["brand"]
                item["located_in_wikidata"] = CircleKSpider.CIRCLE_K["brand_wikidata"]
            elif item["name"] == "City Market":
                item["located_in"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand_wikidata"]
            elif item["name"] == "Costco":
                item["located_in"] = "Costco"
                item["located_in_wikidata"] = COSTCO_SHARED_ATTRIBUTES["brand_wikidata"]
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
                item["located_in"] = FoodCitySoutheastUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = FoodCitySoutheastUSSpider.item_attributes["brand_wikidata"]
            elif item["name"] == "Fred Meyer":
                item["located_in"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand_wikidata"]
            elif item["name"] == "Fry's":
                item["located_in"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand_wikidata"]
            elif item["name"] == "Giant Food":
                item["located_in"] = GiantFoodUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = GiantFoodUSSpider.item_attributes["brand_wikidata"]
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
                item["located_in"] = MarketBasketUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = MarketBasketUSSpider.item_attributes["brand_wikidata"]
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
                item["located_in"] = ShopriteUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = ShopriteUSSpider.item_attributes["brand_wikidata"]
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
                item["located_in"] = WegmansUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WegmansUSSpider.item_attributes["brand_wikidata"]
=======
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item["name"] or "", LOCATION_MAPPINGS, self
            )
>>>>>>> master:locations/spiders/bmo.py
        else:
            self.logger.error("Unknown location type: %s", location["grouptype"])

        yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            open_time = location.get(f"{day.lower()}_open")
            close_time = location.get(f"{day.lower()}_close")
            if open_time and close_time:
                oh.add_range(day, open_time, close_time)
        return oh
