from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.albertsons import AlbertsonsSpider
from locations.spiders.ampm_us import AmpmUSSpider
from locations.spiders.caseys_general_store import CaseysGeneralStoreSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.costco_ca_gb_us import COSTCO_SHARED_ATTRIBUTES
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.giant_food_stores import GiantFoodStoresSpider
from locations.spiders.h_e_b_us import HEBUSSpider
from locations.spiders.kroger_us import BRANDS as KROGER_BRANDS
from locations.spiders.mapco_us import MapcoUSSpider
from locations.spiders.race_trac_us import RaceTracUSSpider
from locations.spiders.royal_farms import RoyalFarmsSpider
from locations.spiders.safeway import SafewaySpider
from locations.spiders.seven_eleven_ca_us import SevenElevenCAUSSpider
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.wawa import WawaSpider
from locations.spiders.wegmans_us import WegmansUSSpider
from locations.spiders.winn_dixie_us import WinnDixieUSSpider


class AllpointSpider(Spider):
    name = "allpoint"
    item_attributes = {"network": "Allpoint", "network_wikidata": "Q4733264"}
    total_count = 0
    page_size = 0
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://clsws.locatorsearch.net/Rest/LocatorSearchAPI.svc/GetLocations",
            data={
                "NetworkId": 10029,
                "Latitude": 33.15004936,
                "Longitude": -96.83464,
                "Miles": 50000,
                "SearchByOptions": "ATMSF, ATMDP",
                "PageIndex": page,
            },
            cb_kwargs={"current_page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        results = response.json()["data"]
        if not self.total_count:
            # Initialize total_count and page_size only once, when data is available
            self.total_count = results["TotalRecCount"]
            self.page_size = results["PageSize"]

        locations = results.get("ATMInfo") or []
        for atm in locations:
            item = DictParser.parse(atm)
            item["street_address"] = item.pop("street", None)

            # Allpoint is a network, not an operator
            # Note: API does not provide operator information (who owns/operates the ATM)
            # ATMs are operated by various banks (Citibank, Capital One, etc.) but this data is not available
            apply_category(Categories.ATM, item)

            # Map retail outlet to located_in
            retail_outlet = atm.get("RetailOutlet", "")
            if retail_outlet == "CVS":
                item["located_in"] = CVS_BRANDS["CVS Pharmacy"]["brand"]
                item["located_in_wikidata"] = CVS_BRANDS["CVS Pharmacy"]["brand_wikidata"]
            elif retail_outlet == "Walgreens":
                item["located_in"] = WalgreensSpider.WALGREENS["brand"]
                item["located_in_wikidata"] = WalgreensSpider.WALGREENS["brand_wikidata"]
            elif retail_outlet == "Alon 7-Eleven" or retail_outlet == "7-Eleven":
                item["located_in"] = SevenElevenCAUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SevenElevenCAUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Target":
                item["located_in"] = TargetUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = TargetUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Costco" or retail_outlet == "Costco Wholesale":
                item["located_in"] = "Costco"
                item["located_in_wikidata"] = COSTCO_SHARED_ATTRIBUTES["brand_wikidata"]
            elif retail_outlet == "Kroger":
                item["located_in"] = KROGER_BRANDS["https://www.kroger.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.kroger.com/"]["brand_wikidata"]
            elif retail_outlet == "Racetrac" or retail_outlet == "RaceTrac":
                item["located_in"] = RaceTracUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RaceTracUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Casey's":
                item["located_in"] = CaseysGeneralStoreSpider.item_attributes["brand"]
                item["located_in_wikidata"] = CaseysGeneralStoreSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Heb" or retail_outlet == "H-E-B":
                item["located_in"] = HEBUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = HEBUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Circle K":
                item["located_in"] = CircleKSpider.CIRCLE_K["brand"]
                item["located_in_wikidata"] = CircleKSpider.CIRCLE_K["brand_wikidata"]
            elif retail_outlet == "Tom Thumb":
                item["located_in"] = AlbertsonsSpider.brands["tomthumb"]["brand"]
                item["located_in_wikidata"] = AlbertsonsSpider.brands["tomthumb"]["brand_wikidata"]
            elif retail_outlet == "Safeway":
                item["located_in"] = SafewaySpider.item_attributes["brand"]
                item["located_in_wikidata"] = SafewaySpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Mapco":
                item["located_in"] = MapcoUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = MapcoUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Speedway":
                item["located_in"] = SpeedwayUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SpeedwayUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet in ["Wawa", "Wawa 1", "Wawa 2"]:
                item["located_in"] = WawaSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WawaSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Ampm":
                item["located_in"] = AmpmUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = AmpmUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Chevron":
                item["located_in"] = CHEVRON_BRANDS["Chevron"][0]["brand"]
                item["located_in_wikidata"] = CHEVRON_BRANDS["Chevron"][0]["brand_wikidata"]
            elif retail_outlet == "Giant Food":
                item["located_in"] = GiantFoodStoresSpider.item_attributes["brand"]
                item["located_in_wikidata"] = GiantFoodStoresSpider.item_attributes["brand_wikidata"]
            elif retail_outlet in ["Royal Farms", "Royal Farms 1", "Royal Farms 2"]:
                item["located_in"] = RoyalFarmsSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RoyalFarmsSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Getgo" or retail_outlet == "GetGo":
                item["located_in"] = GiantEagleUSSpider.GET_GO["brand"]
                item["located_in_wikidata"] = GiantEagleUSSpider.GET_GO["brand_wikidata"]
            elif retail_outlet == "Harris Teeter":
                item["located_in"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand"]
                item["located_in_wikidata"] = KROGER_BRANDS["https://www.harristeeter.com/"]["brand_wikidata"]
            elif retail_outlet == "Winn Dixie":
                item["located_in"] = WinnDixieUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WinnDixieUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Sunoco":
                item["located_in"] = SunocoUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SunocoUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Wegmans":
                item["located_in"] = WegmansUSSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WegmansUSSpider.item_attributes["brand_wikidata"]
            elif retail_outlet == "Duane Reade":
                item["located_in"] = WalgreensSpider.DUANE_READE["brand"]
                item["located_in_wikidata"] = WalgreensSpider.DUANE_READE["brand_wikidata"]

            yield item

        if (kwargs["current_page"] * self.page_size) < self.total_count:
            yield self.make_request(kwargs["current_page"] + 1)
