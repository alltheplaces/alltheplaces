import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.searchable_points import open_searchable_points
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.ampm_us import AmpmUSSpider
from locations.spiders.brookshires_us import BrookshiresUSSpider
from locations.spiders.capital_one import CapitalOneSpider
from locations.spiders.caseys_general_store import CaseysGeneralStoreSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.costco_ca_gb_us import COSTCO_SHARED_ATTRIBUTES
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.eg_america_us import EgAmericaUSSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.food_city_southeast_us import FoodCitySoutheastUSSpider
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.giant_food_us import GiantFoodUSSpider
from locations.spiders.h_e_b_us import HEBUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.kwik_trip import BRANDS as KWIK_TRIP_BRANDS
from locations.spiders.mapco_us import MapcoUSSpider
from locations.spiders.marcs import MarcsSpider
from locations.spiders.market_basket_us import MarketBasketUSSpider
from locations.spiders.mountain_america_credit_union_us import MountainAmericaCreditUnionUSSpider
from locations.spiders.peoples_bank_us import PeoplesBankUSSpider
from locations.spiders.pnc_bank_us import PncBankUSSpider
from locations.spiders.quickchek_us import QuickchekUSSpider
from locations.spiders.race_trac_us import RaceTracUSSpider
from locations.spiders.royal_farms import RoyalFarmsSpider
from locations.spiders.safeway import SafewaySpider
from locations.spiders.seven_eleven_ca_us import SevenElevenCAUSSpider
from locations.spiders.sheetz import SheetzSpider
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.united_dairy_farmers_us import UnitedDairyFarmersUSSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.wawa import WawaSpider
from locations.spiders.wegmans_us import WegmansUSSpider
from locations.spiders.winn_dixie_us import WinnDixieUSSpider


class CitiSpider(Spider):
    name = "citi"
    item_attributes = {"brand": "Citibank", "brand_wikidata": "Q857063"}
    allowed_domains = ["citi.com"]
    custom_settings = {"DOWNLOAD_DELAY": 1.5}

    MONEY_PASS_NETWORK = {"network": "MoneyPass", "network_wikidata": "Q28447513"}

    BANK_OPERATORS = {
        "PNC BANK": {
            "brand": PncBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PncBankUSSpider.item_attributes["brand_wikidata"],
        },
        "PNC AT WAWA": {
            "brand": PncBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PncBankUSSpider.item_attributes["brand_wikidata"],
        },
        "PNC AT SHEETZ": {
            "brand": PncBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PncBankUSSpider.item_attributes["brand_wikidata"],
        },
        "PNC AT QUICKCHEK": {
            "brand": PncBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PncBankUSSpider.item_attributes["brand_wikidata"],
        },
        "PNC AT UDF": {
            "brand": PncBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PncBankUSSpider.item_attributes["brand_wikidata"],
        },
        "PEOPLES BANK": {
            "brand": PeoplesBankUSSpider.item_attributes["brand"],
            "brand_wikidata": PeoplesBankUSSpider.item_attributes["brand_wikidata"],
        },
        "CAPITAL CITY BANK": {"brand": "Capital City Bank", "brand_wikidata": "Q5035079"},
        "FIRST INTERSTATE BANK 09": {"brand": "First Interstate Bank", "brand_wikidata": "Q5453107"},
        "SIMMONS BANK": {"brand": "Simmons Bank", "brand_wikidata": "Q28402389"},
        "ASSOCIATED BANK": {"brand": "Associated Bank", "brand_wikidata": "Q4809155"},
        "MOUNTAIN AMERICA CU": {
            "brand": MountainAmericaCreditUnionUSSpider.item_attributes["brand"],
            "brand_wikidata": MountainAmericaCreditUnionUSSpider.item_attributes["brand_wikidata"],
        },
        "ONPOINT COMMUNITY CREDIT UNION": {"brand": "OnPoint", "brand_wikidata": "Q107802623"},
        "BUSEY BANK": {"brand": "Busey Bank", "brand_wikidata": "Q5001347"},
        "HOMESTREET BANK": {"brand": "HomeStreet Bank", "brand_wikidata": "Q60762481"},
        "EAST WEST BANK": {"brand": "East West Bank", "brand_wikidata": "Q3046549"},
        "FIDELITY BANK": {"brand": "Fidelity Bank", "brand_wikidata": "Q27883293"},
        "SOUTHERN BANK": {"brand": "Southern Bank", "brand_wikidata": "Q130551561"},
        "WEBSTER BANK": {"brand": "WebsterBank", "brand_wikidata": "Q7978891"},
        "CENTRAL BANK": {"brand": "Central Bank", "brand_wikidata": "Q113482320"},
        "FARMERS NATIONAL BANK": {"brand": "Farmers National Bank", "brand_wikidata": "Q104126232"},
        "NICOLET NATIONAL BANK": {"brand": "Nicolet National Bank", "brand_wikidata": "Q124021408"},
        "WASHINGTON FEDERAL BANK": {"brand": "WaFd Bank", "brand_wikidata": "Q7971859"},
        "FIRST MERCHANTS BANK": {"brand": "First Merchants Bank", "brand_wikidata": "Q19572527"},
        "WINGS FINANCIAL": {"brand": "Wings Financial Credit Union", "brand_wikidata": "Q8025267"},
        "CNB BANK": {"brand": "City National Bank", "brand_wikidata": "Q134008763"},
        "REPUBLIC BANK & TRUST CO": {"brand": "Republic Bank", "brand_wikidata": "Q7314387"},
        "FIRSTBANK": {"brand": "First Bank", "brand_wikidata": "Q5452332"},
        "CAPITAL ONE": {
            "brand": CapitalOneSpider.item_attributes["brand"],
            "brand_wikidata": CapitalOneSpider.item_attributes["brand_wikidata"],
        },
    }

    headers = {"client_id": "4a51fb19-a1a7-4247-bc7e-18aa56dd1c40"}

    def set_atm_operator(self, properties: dict, name: str) -> None:
        if match := re.match(r"^ATM (.+)$", name):
            atm_suffix = match.group(1)
            atm_suffix_upper = atm_suffix.upper()

            if atm_suffix_upper in self.BANK_OPERATORS:
                properties["operator"] = self.BANK_OPERATORS[atm_suffix_upper]["brand"]
                properties["operator_wikidata"] = self.BANK_OPERATORS[atm_suffix_upper]["brand_wikidata"]
                properties["brand"] = self.BANK_OPERATORS[atm_suffix_upper]["brand"]
                properties["brand_wikidata"] = self.BANK_OPERATORS[atm_suffix_upper]["brand_wikidata"]
            elif any(keyword in atm_suffix_upper for keyword in ["BANK", "CREDIT UNION", " FCU", "CU", "FINANCIAL"]):
                # The ATM is operated by another unmapped bank. Removing the brand and operator so it's not set to Citi.
                properties["operator"] = ""
                properties["operator_wikidata"] = ""
                properties["brand"] = ""
                properties["brand_wikidata"] = ""
            else:
                # No bank detected. Set operator and brand to an empty string if it wasn't set before to avoid setting
                # the defaults. This is relevant for MoneyPass ATMs that shouldn't be Citi-branded.
                if "operator" not in properties:
                    properties["operator"] = ""
                    properties["operator_wikidata"] = ""
                if "brand" not in properties:
                    properties["brand"] = ""
                    properties["brand_wikidata"] = ""

    def set_atm_located_in(self, properties: dict, name: str) -> None:
        name_upper = name.upper()

        if "WAWA" in name_upper:
            properties["located_in"] = WawaSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = WawaSpider.item_attributes["brand_wikidata"]
        elif "SHEETZ" in name_upper:
            properties["located_in"] = SheetzSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = SheetzSpider.item_attributes["brand_wikidata"]
        elif "UDF" in name_upper:
            properties["located_in"] = UnitedDairyFarmersUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = UnitedDairyFarmersUSSpider.item_attributes["brand_wikidata"]
        elif "QUICKCHEK" in name_upper:
            properties["located_in"] = QuickchekUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = QuickchekUSSpider.item_attributes["brand_wikidata"]
        elif "7ELEVEN" in name_upper or "7-ELEVEN" in name_upper:
            properties["located_in"] = SevenElevenCAUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = SevenElevenCAUSSpider.item_attributes["brand_wikidata"]
        elif "WALGREENS" in name_upper:
            properties["located_in"] = WalgreensSpider.WALGREENS["brand"]
            properties["located_in_wikidata"] = WalgreensSpider.WALGREENS["brand_wikidata"]
        elif "CVS" in name_upper:
            properties["located_in"] = CVS_BRANDS["CVS Pharmacy"]["brand"]
            properties["located_in_wikidata"] = CVS_BRANDS["CVS Pharmacy"]["brand_wikidata"]
        elif "CIRCLE K" in name_upper or "CIRCLEK" in name_upper:
            properties["located_in"] = CircleKSpider.CIRCLE_K["brand"]
            properties["located_in_wikidata"] = CircleKSpider.CIRCLE_K["brand_wikidata"]
        elif "SPEEDWAY" in name_upper:
            properties["located_in"] = SpeedwayUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = SpeedwayUSSpider.item_attributes["brand_wikidata"]
        elif "TARGET" in name_upper:
            properties["located_in"] = TargetUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = TargetUSSpider.item_attributes["brand_wikidata"]
        elif "CASEY" in name_upper:
            properties["located_in"] = CaseysGeneralStoreSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = CaseysGeneralStoreSpider.item_attributes["brand_wikidata"]
        elif "COSTCO" in name_upper:
            properties["located_in"] = "Costco"
            properties["located_in_wikidata"] = COSTCO_SHARED_ATTRIBUTES["brand_wikidata"]
        elif "AMPM" in name_upper:
            properties["located_in"] = AmpmUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = AmpmUSSpider.item_attributes["brand_wikidata"]
        elif "MAPCO" in name_upper:
            properties["located_in"] = MapcoUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = MapcoUSSpider.item_attributes["brand_wikidata"]
        elif "CERTIFIED" in name_upper:
            properties["located_in"] = "Certified"
            properties["located_in_wikidata"] = "Q100148356"
        elif "KROGER" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.kroger.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.kroger.com/"]["brand_wikidata"]
        elif "HARRIS TEETER" in name_upper or "HARRISTEETER" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand_wikidata"]
        elif "ROYAL FARMS" in name_upper:
            properties["located_in"] = RoyalFarmsSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = RoyalFarmsSpider.item_attributes["brand_wikidata"]
        elif "HEB" in name_upper or "H-E-B" in name_upper:
            properties["located_in"] = HEBUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = HEBUSSpider.item_attributes["brand_wikidata"]
        elif "SAFEWAY" in name_upper:
            properties["located_in"] = SafewaySpider.item_attributes["brand"]
            properties["located_in_wikidata"] = SafewaySpider.item_attributes["brand_wikidata"]
        elif "WEGMANS" in name_upper:
            properties["located_in"] = WegmansUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = WegmansUSSpider.item_attributes["brand_wikidata"]
        elif "GIANT EAGLE" in name_upper:
            properties["located_in"] = GiantEagleUSSpider.GIANT_EAGLE["brand"]
            properties["located_in_wikidata"] = GiantEagleUSSpider.GIANT_EAGLE["brand_wikidata"]
        elif "GETGO" in name_upper or "GET GO" in name_upper:
            properties["located_in"] = GiantEagleUSSpider.GET_GO["brand"]
            properties["located_in_wikidata"] = GiantEagleUSSpider.GET_GO["brand_wikidata"]
        elif "MARCS" in name_upper:
            properties["located_in"] = MarcsSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = MarcsSpider.item_attributes["brand_wikidata"]
        elif "FRED MEYER" in name_upper or "FREDMEYER" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.fredmeyer.com/"]["brand_wikidata"]
        elif "QFC" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.qfc.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.qfc.com/"]["brand_wikidata"]
        elif "FOOD 4 LESS" in name_upper or "FOOD4LESS" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.food4less.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.food4less.com/"]["brand_wikidata"]
        elif "RALPH" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.ralphs.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.ralphs.com/"]["brand_wikidata"]
        elif "FRY" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.frysfood.com/"]["brand_wikidata"]
        elif "SMITH" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.smithsfoodanddrug.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.smithsfoodanddrug.com/"]["brand_wikidata"]
        elif "CITY MARKET" in name_upper or "CITYMARKET" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.citymarket.com/"]["brand_wikidata"]
        elif "DILLONS" in name_upper:
            properties["located_in"] = KROGER_BRANDS["https://www.dillons.com/"]["brand"]
            properties["located_in_wikidata"] = KROGER_BRANDS["https://www.dillons.com/"]["brand_wikidata"]
        elif "FOOD CITY" in name_upper or "FOODCITY" in name_upper:
            properties["located_in"] = FoodCitySoutheastUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = FoodCitySoutheastUSSpider.item_attributes["brand_wikidata"]
        elif "QUIK STOP" in name_upper or "QUIKSTOP" in name_upper:
            properties["located_in"] = EgAmericaUSSpider.brands[11]["brand"]
            properties["located_in_wikidata"] = EgAmericaUSSpider.brands[11]["brand_wikidata"]
        elif "GIANT FOOD" in name_upper:
            properties["located_in"] = GiantFoodUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = GiantFoodUSSpider.item_attributes["brand_wikidata"]
        elif "EXXON" in name_upper:
            properties["located_in"] = ExxonMobilSpider.brands["Exxon"]["brand"]
            properties["located_in_wikidata"] = ExxonMobilSpider.brands["Exxon"]["brand_wikidata"]
        elif "RACETRAC" in name_upper or "RACE TRAC" in name_upper:
            properties["located_in"] = RaceTracUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = RaceTracUSSpider.item_attributes["brand_wikidata"]
        elif "WINN DIXIE" in name_upper or "WINNDIXIE" in name_upper or "WINN-DIXIE" in name_upper:
            properties["located_in"] = WinnDixieUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = WinnDixieUSSpider.item_attributes["brand_wikidata"]
        elif "TOM THUMB" in name_upper or "TOMTHUMB" in name_upper:
            properties["located_in"] = AlbertsonsSpider.brands["tomthumb"]["brand"]
            properties["located_in_wikidata"] = AlbertsonsSpider.brands["tomthumb"]["brand_wikidata"]
        elif "CHEVRON" in name_upper:
            properties["located_in"] = CHEVRON_BRANDS["Chevron"][0]["brand"]
            properties["located_in_wikidata"] = CHEVRON_BRANDS["Chevron"][0]["brand_wikidata"]
        elif "KWIK SHOP" in name_upper or "KWIKSHOP" in name_upper:
            properties["located_in"] = EgAmericaUSSpider.brands[18]["brand"]
            properties["located_in_wikidata"] = EgAmericaUSSpider.brands[18]["brand_wikidata"]
        elif "LOAF 'N JUG" in name_upper or "LOAF N JUG" in name_upper or "LOAFNJUG" in name_upper:
            properties["located_in"] = EgAmericaUSSpider.brands[19]["brand"]
            properties["located_in_wikidata"] = EgAmericaUSSpider.brands[19]["brand_wikidata"]
        elif "SUNOCO" in name_upper:
            properties["located_in"] = SunocoUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = SunocoUSSpider.item_attributes["brand_wikidata"]
        elif "MARKET BASKET" in name_upper or "MARKETBASKET" in name_upper:
            properties["located_in"] = MarketBasketUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = MarketBasketUSSpider.item_attributes["brand_wikidata"]
        elif "VONS" in name_upper:
            properties["located_in"] = AlbertsonsSpider.brands["vons"]["brand"]
            properties["located_in_wikidata"] = AlbertsonsSpider.brands["vons"]["brand_wikidata"]
        elif "BROOKSHIRES" in name_upper:
            properties["located_in"] = BrookshiresUSSpider.item_attributes["brand"]
            properties["located_in_wikidata"] = BrookshiresUSSpider.item_attributes["brand_wikidata"]
        elif "KWIK STAR" in name_upper:
            properties["located_in"] = KWIK_TRIP_BRANDS["KWIK STAR"]["brand"]
            properties["located_in_wikidata"] = KWIK_TRIP_BRANDS["KWIK STAR"]["brand_wikidata"]
        elif "KWIK TRIP TOBACCO OUTLET" in name_upper:
            properties["located_in"] = KWIK_TRIP_BRANDS["TOBACCO OUTLET PLUS"].get(
                "brand", KWIK_TRIP_BRANDS["TOBACCO OUTLET PLUS"]["name"]
            )
            properties["located_in_wikidata"] = KWIK_TRIP_BRANDS["TOBACCO OUTLET PLUS"].get("brand_wikidata")
        elif "KWIK TRIP" in name_upper:
            properties["located_in"] = KWIK_TRIP_BRANDS["KWIK TRIP"]["brand"]
            properties["located_in_wikidata"] = KWIK_TRIP_BRANDS["KWIK TRIP"]["brand_wikidata"]
        elif "STOP N GO" in name_upper:
            properties["located_in"] = KWIK_TRIP_BRANDS["STOP N GO"].get("brand", KWIK_TRIP_BRANDS["STOP N GO"]["name"])
            properties["located_in_wikidata"] = KWIK_TRIP_BRANDS["STOP N GO"].get("brand_wikidata")

    async def start(self) -> AsyncIterator[JsonRequest]:
        with open_searchable_points("us_centroids_100mile_radius_state.csv") as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(",")
                if state not in {"AK", "HI"}:
                    yield JsonRequest(
                        url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                        headers=self.headers,
                        data={
                            "type": "branchesAndATMs",
                            "inputLocation": [float(lon), float(lat)],
                            "resultCount": "1000",
                            "distanceUnit": "MILE",
                            "findWithinRadius": "100",
                        },
                    )

        # Alaska and Hawaii
        for point in [[-149.318198, 62.925651], [-156.400325, 20.670266]]:
            yield JsonRequest(
                url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                headers=self.headers,
                data={
                    "type": "branchesAndATMs",
                    "inputLocation": point,
                    "resultCount": "1000",
                    "distanceUnit": "MILE",
                    "findWithinRadius": "1000",
                },
            )

    def parse(self, response):
        data = response.json()

        for feature in data["features"]:
            postcode = feature["properties"]["postalCode"]

            # fix 4-digit postcodes :(
            if feature["properties"]["country"] == "united states of america" and postcode:
                postcode = postcode.zfill(5)

            properties = {
                "ref": feature["id"],
                "name": feature["properties"]["name"],
                "street_address": feature["properties"]["addressLine1"].strip(),
                "city": feature["properties"]["city"].title(),
                "state": feature["properties"]["state"].upper(),
                "postcode": postcode,
                "country": feature["properties"]["country"].title(),
                "phone": feature["properties"]["phone"],
                "lat": float(feature["geometry"]["coordinates"][1]),
                "lon": float(feature["geometry"]["coordinates"][0]),
                "extras": {"type": feature["properties"]["type"]},
            }

            additional = feature["properties"].get("additionalProperties", {})

            if feature["properties"]["type"] in ["atm", "moneypassatm"]:
                apply_category(Categories.ATM, properties)
                name = properties["name"]

                if feature["properties"]["type"] == "atm":
                    properties["operator"] = self.item_attributes["brand"]
                    properties["operator_wikidata"] = self.item_attributes["brand_wikidata"]
                    properties["brand"] = self.item_attributes["brand"]
                    properties["brand_wikidata"] = self.item_attributes["brand_wikidata"]
                elif feature["properties"]["type"] == "moneypassatm":
                    properties.update(self.MONEY_PASS_NETWORK)

                self.set_atm_operator(properties, name)
                self.set_atm_located_in(properties, name)

                apply_yes_no(Extras.CASH_IN, properties, not additional.get("withdrawalsOnly", True))

            elif feature["properties"]["type"] in ["branch", "citifinancial", "private bank"]:
                apply_category(Categories.BANK, properties)
                apply_yes_no(Extras.ATM, properties, additional.get("hasATM") or additional.get("atm24HR"))

            apply_yes_no(Extras.WHEELCHAIR, properties, additional.get("Wheelchair") or additional.get("ADA"))
            apply_yes_no("speech_output", properties, additional.get("TalkingATM"))
            apply_yes_no(
                Extras.DRIVE_THROUGH, properties, additional.get("DriveUpTeller") or additional.get("driveupATM")
            )

            yield Feature(**properties)
