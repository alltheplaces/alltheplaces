from copy import deepcopy
from typing import AsyncIterator, Iterable

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

# POI Types mapping found in https://dlo.api.bmw/main.js
"""
{
  "newCars": [{ "type": "distributionBranches", "key": "F" }],
  "usedCars": [{ "type": "distributionBranches", "key": "G" }],
  "repairServices": [{ "type": "distributionBranches", "key": "T" }],
  "mCertified": [{ "type": "businessTypes", "key": "MC" }],
  "classicCertified": [{ "type": "businessTypes", "key": "CC" }],
  "eRetail": [{ "type": "requestServices", "key": "SON" }],
  "highVoltageServices": [{ "type": "services", "key": "HV" }],
  "carbonServices": [{ "type": "services", "key": "CR" }],
  "bodyShop": [{ "type": "requestServices", "key": "CBS" }],
  "paintShop": [{ "type": "requestServices", "key": "CPS" }],
  "onlineBooking": [{ "type": "testDriveBooking", "key": "TDB_OB" }],
  "sendRequest": [{ "type": "testDriveBooking", "key": "TDB_SR" }],
  "bmwEmployeeDelivery": [{ "type": "businessTypes", "key": "GE" }]
}
"""


class BmwGroupSpider(Spider):
    name = "bmw_group"
    BMW_MOTORBIKE = "BMW_MOTORBIKE"
    BRAND_MAPPING = {
        "BMW": {"brand": "BMW", "brand_wikidata": "Q26678"},
        "ROLLS_ROYCE": {"brand": "Rolls-Royce", "brand_wikidata": "Q234803"},
        "MINI": {"brand": "Mini", "brand_wikidata": "Q116232"},
        BMW_MOTORBIKE: {"brand": "BMW Motorrad", "brand_wikidata": "Q249173"},
    }

    async def start(self) -> AsyncIterator[Request]:
        for country in GeonamesCache().get_countries().keys():
            url = f"https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/-/pois?cached=off&language=en&lat=0&lng=0&maxResults=10000&unit=km&showAll=true&country={country}"
            yield Request(
                url=url, callback=self.parse, headers={"Accept": "application/json", "Content-Type": "application/json"}
            )

    def parse(self, response):
        if response.status == 204:
            self.logger.info(f"No content found in {response.url}")
        else:
            response = response.json().get("data").get("pois")
            for data in response:
                data["street_address"] = data.pop("street")

                item = DictParser.parse(data)
                item["ref"] = f"{data.get('key', '')}-{data.get('category', '')}"
                item["phone"] = data.get("attributes", {}).get("phone")
                item["email"] = data.get("attributes", {}).get("mail")
                item["website"] = data.get("attributes", {}).get("homepage")

                if match := self.BRAND_MAPPING.get(data.get("category")):
                    item.update(match)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/brand/fail/{data.get('category')}")
                    self.logger.error(f"Unknown brand: {data.get('category')}, {item['ref']}")

                yield from self.map_categories(item, data)

    def map_categories(self, item: Feature, poi: dict) -> Iterable[Feature]:
        distribution_branches = poi.get("attributes", {}).get("distributionBranches", [])
        category = poi.get("category")

        if category == self.BMW_MOTORBIKE:
            return self.apply_motorbike_category(item, distribution_branches)
        else:
            return self.apply_car_category(item, distribution_branches)

    def apply_motorbike_category(self, item: Feature, distribution_branches: list) -> Iterable[Feature]:
        shop_item = None
        service_item = None
        if "F" in distribution_branches or "G" in distribution_branches:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            apply_category(Categories.SHOP_MOTORCYCLE, shop_item)
            apply_yes_no(Extras.USED_MOTORCYCLE_SALES, shop_item, "G" in distribution_branches)
            apply_yes_no(
                Extras.MOTORCYCLE_REPAIR, shop_item, "T" in distribution_branches or "CCRC" in distribution_branches
            )
            yield shop_item

        if "T" in distribution_branches or "CCRC" in distribution_branches:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_MOTORCYCLE_REPAIR, service_item)
            yield service_item

        if not shop_item and not service_item:
            self.log_unknown_branches(distribution_branches, item)

    def apply_car_category(self, item: Feature, distribution_branches: list) -> Iterable[Feature]:
        shop_item = None
        service_item = None
        if "F" in distribution_branches or "G" in distribution_branches:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            apply_category(Categories.SHOP_CAR, shop_item)
            apply_yes_no(Extras.USED_CAR_SALES, shop_item, "G" in distribution_branches)
            apply_yes_no(Extras.CAR_REPAIR, shop_item, "T" in distribution_branches or "CCRC" in distribution_branches)
            yield shop_item

        if "T" in distribution_branches or "CCRC" in distribution_branches:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        if not shop_item and not service_item:
            self.log_unknown_branches(distribution_branches, item)

    def log_unknown_branches(self, distribution_branches: list, item: Feature):
        for branch in distribution_branches:
            self.crawler.stats.inc_value(f"atp/{self.name}/distribution_branch/fail/{branch}")
            self.logger.error(f"Unknown distribution branch: {branch}, {item['ref']}")
