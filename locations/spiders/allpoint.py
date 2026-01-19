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

    LOCATED_IN_MAPPINGS = {
        "CVS": CVS_BRANDS["CVS Pharmacy"],
        "Walgreens": WalgreensSpider.WALGREENS,
        "Alon 7-Eleven": SevenElevenCAUSSpider.item_attributes,
        "7-Eleven": SevenElevenCAUSSpider.item_attributes,
        "Target": TargetUSSpider.item_attributes,
        "Costco": {"brand": "Costco", "brand_wikidata": COSTCO_SHARED_ATTRIBUTES["brand_wikidata"]},
        "Costco Wholesale": {"brand": "Costco", "brand_wikidata": COSTCO_SHARED_ATTRIBUTES["brand_wikidata"]},
        "Kroger": KROGER_BRANDS["https://www.kroger.com/"],
        "Racetrac": RaceTracUSSpider.item_attributes,
        "RaceTrac": RaceTracUSSpider.item_attributes,
        "Casey's": CaseysGeneralStoreSpider.item_attributes,
        "Heb": HEBUSSpider.item_attributes,
        "H-E-B": HEBUSSpider.item_attributes,
        "Circle K": CircleKSpider.CIRCLE_K,
        "Tom Thumb": AlbertsonsSpider.brands["tomthumb"],
        "Safeway": SafewaySpider.item_attributes,
        "Mapco": MapcoUSSpider.item_attributes,
        "Speedway": SpeedwayUSSpider.item_attributes,
        "Wawa": WawaSpider.item_attributes,
        "Wawa 1": WawaSpider.item_attributes,
        "Wawa 2": WawaSpider.item_attributes,
        "Ampm": AmpmUSSpider.item_attributes,
        "Chevron": CHEVRON_BRANDS["Chevron"][0],
        "Giant Food": GiantFoodStoresSpider.item_attributes,
        "Royal Farms": RoyalFarmsSpider.item_attributes,
        "Royal Farms 1": RoyalFarmsSpider.item_attributes,
        "Royal Farms 2": RoyalFarmsSpider.item_attributes,
        "Getgo": GiantEagleUSSpider.GET_GO,
        "GetGo": GiantEagleUSSpider.GET_GO,
        "Harris Teeter": KROGER_BRANDS["https://www.harristeeter.com/"],
        "Winn Dixie": WinnDixieUSSpider.item_attributes,
        "Sunoco": SunocoUSSpider.item_attributes,
        "Wegmans": WegmansUSSpider.item_attributes,
        "Duane Reade": WalgreensSpider.DUANE_READE,
    }

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
            if retail_outlet and retail_outlet in self.LOCATED_IN_MAPPINGS:
                brand_data = self.LOCATED_IN_MAPPINGS[retail_outlet]
                item["located_in"] = brand_data["brand"]
                item["located_in_wikidata"] = brand_data.get("brand_wikidata")

            yield item

        if (kwargs["current_page"] * self.page_size) < self.total_count:
            yield self.make_request(kwargs["current_page"] + 1)
