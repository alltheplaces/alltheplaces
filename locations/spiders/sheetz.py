from enum import Enum

import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

FEATURES_MAPPING = {
    "alcohol": None,
    "atm": Extras.ATM,
    "bulkDef": None,
    "carWash": Extras.CAR_WASH,
    "delivery": Extras.DELIVERY,
    "driveThru": Extras.DRIVE_THROUGH,
    "diesel": Fuel.DIESEL,
    "e0": Fuel.ETHANOL_FREE,
    "e15": Fuel.E15,
    "e85": Fuel.E85,
    "freeWifi": Extras.WIFI,
    # TODO: map high flow auto diesel
    "highFlowAutoDiesel": None,
    "highFlowDiesel": Fuel.HGV_DIESEL,
    "kerosene": Fuel.KEROSENE,
    "propane": Fuel.PROPANE,
    "pncAtm": Extras.ATM,
    "showers": Extras.SHOWERS,
    "truckDieselLanes": None,
    # TODO: map truck scales as amenity=weighbridge and yield as a separate item.
    "truckScales": None,
    "truckParking": None,
    "truckParkingSpots": None,
}


class SheetzSpider(scrapy.Spider):
    name = "sheetz"
    item_attributes = {"brand": "Sheetz", "brand_wikidata": "Q7492551"}
    allowed_domains = ["orders.sheetz.com"]
    start_urls = ["https://orders.sheetz.com/anybff/api/stores/getOperatingStates"]
    user_agent = BROWSER_DEFAULT

    def make_request(self, state, page=0):
        return scrapy.http.JsonRequest(
            f"https://orders.sheetz.com/anybff/api/stores/search?stateCode={state}&page={page}&size=15",
            data={},
            callback=self.parse_stores,
            meta={"state": state, "page": page},
        )

    def parse(self, response):
        for state in response.json()["states"].keys():
            yield self.make_request(state)

    def parse_stores(self, response):
        if store := response.json()["stores"]:
            for store in store:
                store["street-address"] = store.pop("address")
                item = DictParser.parse(store)
                item["ref"] = store.get("storeNumber")
                item["website"] = f'https://orders.sheetz.com/findASheetz/store/{store["storeNumber"]}'
                item["image"] = f'https://orders.sheetz.com{store.get("imageUrl")}'
                features = store.get("features", {})
                self.parse_features(item, features)
                self.parse_24_7(item, features)
                apply_category(Categories.FUEL_STATION, item)
                yield item
            yield self.make_request(response.meta["state"], 1 + response.meta["page"])

    def parse_features(self, item: Feature, features: dict):
        for k, v in features.items():
            if tag := FEATURES_MAPPING.get(k):
                if isinstance(v, bool):
                    apply_yes_no(tag, item, v)
                elif isinstance(v, int):
                    apply_yes_no(f"{tag.value if isinstance(tag, Enum) else tag}={v}", item, True)
            else:
                # self.crawler.stats.inc_value(f"atp/sheetz/feature/failed/{k}")
                continue

    def parse_24_7(self, item: Feature, features: dict):
        if features.get("open24x7"):
            oh = OpeningHours()
            oh.add_days_range(DAYS, "00:00", "23:59")
            item["opening_hours"] = oh.as_opening_hours()

    # TODO: Below method is not active yet.
    #       At some point we will change it and make it yield a separate item for charging station.
    def parse_charging_station(self, item: Feature, features: dict):
        if features.get("evCharger"):
            apply_category(Categories.CHARGING_STATION, item)

        if features.get("evTeslaSupercharger"):
            apply_category(Categories.CHARGING_STATION, item)
            apply_yes_no("socket:tesla_supercharger", item, True)

        if features.get("evChaDemoDcFastCharging"):
            apply_category(Categories.CHARGING_STATION, item)
            apply_yes_no("socket:chademo", item, True)

        if features.get("evCcsDcFastCharging"):
            apply_category(Categories.CHARGING_STATION, item)
            # All POIs are in US so assume type1_combo socket
            apply_yes_no("socket:type1_combo", item, True)
