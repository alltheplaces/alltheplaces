from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.bargain_booze_gb import BargainBoozeGBSpider
from locations.spiders.bestone_gb import BestoneGBSpider
from locations.spiders.budgens_gb import BudgensGBSpider
from locations.spiders.costcutter_gb import CostcutterGBSpider
from locations.spiders.family_shopper_gb import FamilyShopperGBSpider
from locations.spiders.keystore_gb import KeystoreGBSpider
from locations.spiders.londis_gb import LondisGBSpider
from locations.spiders.morrisons_gb import MorrisonsGBSpider
from locations.spiders.nisalocal_gb import NisalocalGBSpider
from locations.spiders.one_stop_gb import OneStopGBSpider
from locations.spiders.premier_gb import PremierGBSpider
from locations.spiders.spar_gb import SparGBSpider
from locations.spiders.usave_gb import UsaveGBSpider


class PaypointGBSpider(Spider):
    name = "paypoint_gb"
    item_attributes = {"brand": "PayPoint", "brand_wikidata": "Q7156561"}
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_TIMEOUT": 120}

    LOCATED_IN_MAPPINGS = [
        (["PREMIER", "PREMIER STORES", "PREMIER STORE", "PREMIER EXPRESS"], PremierGBSpider.item_attributes, "equals"),
        (["COSTCUTTER"], CostcutterGBSpider.item_attributes),
        (["LONDIS"], LondisGBSpider.item_attributes),
        (["SPAR"], SparGBSpider.item_attributes),
        (["BEST ONE"], BestoneGBSpider.item_attributes),
        (["BUDGENS"], BudgensGBSpider.item_attributes),
        (["NISA"], NisalocalGBSpider.item_attributes),
        (["ONE STOP"], OneStopGBSpider.item_attributes),
        (["FAMILY SHOPPER"], FamilyShopperGBSpider.item_attributes),
        (["MORRISONS DAILY"], MorrisonsGBSpider.MORRISONS_DAILY),
        (["BARGAIN BOOZE"], BargainBoozeGBSpider.item_attributes),
        (["KEYSTORE"], KeystoreGBSpider.item_attributes),
        (["USAVE", "U-SAVE"], UsaveGBSpider.item_attributes),
        (["GO LOCAL"], {"brand": "Go Local", "brand_wikidata": "Q120634011"}),
        (["LIFESTYLE EXPRESS"], {"brand": "Lifestyle Express", "brand_wikidata": "Q61994869"}),
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("GB", 15000):
            yield JsonRequest(
                url="https://www.paypoint.com/umbraco/surface/StoreLocatorSurface/StoreLocator",
                data={
                    "searchCriteria": f'{city["latitude"]},{city["longitude"]}',
                    "product": "ATM",  # null values for product/siteServices returns lower count for ATMs
                    "siteServices": "ATM",
                    "searchType": 6,
                },
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        if locations := response.json().get("ppGroups"):
            for location in locations:
                item = DictParser.parse(location)
                item["ref"] = location.get("SiteNumber")
                item["name"] = self.item_attributes["brand"]
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    location.get("SiteName"), self.LOCATED_IN_MAPPINGS, self
                )
                item["street_address"] = item.pop("addr_full", "")
                services = [service.get("ServiceName").strip() for service in location.get("Services")]
                # products = location.get("OtherProducts")
                # parcel_products = location.get("ParcelProducts")
                if "ATM" in services:
                    apply_category(Categories.ATM, item)
                else:
                    # Not sure about other services whether location can be collected as a PayPoint branded location
                    # https://www.paypoint.com/instore-services
                    continue

                item["opening_hours"] = self.parse_opening_hours(location)
                yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            oh.add_range(day, location[f"{day}Open"], location[f"{day}Close"], "%H%M")
        return oh
