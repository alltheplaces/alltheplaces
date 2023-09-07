from enum import Enum
from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

FEATURES_MAPPING = {
    "alcohol": None,
    'atm': Extras.ATM,
    "bulkDef": None,
    'carWash': Extras.CAR_WASH,
    "delivery": None,
    'driveThru': Extras.DRIVE_THROUGH,
    'diesel': Fuel.DIESEL,
    "e0": Fuel.E0,
    "e15": Fuel.E15,
    "e85": Fuel.E85,
    "freeWifi": Extras.WIFI,
    # TODO: map high flow auto diesel
    "highFlowAutoDiesel": None,
    "highFlowDiesel": Fuel.HGV_DIESEL,
    "kerosene": Fuel.KEROSENE,
    "open24x7": 'opening_hours=24/7',
    "propane": Fuel.PROPANE,
    "pncAtm": Extras.ATM,
    "showers": Extras.SHOWERS,
    "truckDieselLanes": None,
    # TODO: availability of truck scales seems important for trucks
    "truckScales": None,
    "truckParking": None,
    "truckParkingSpots": None,
    "evCcsDcFastCharging": None,
    "evChaDemoDcFastCharging": None,
    "evCharger": None,
    "evTeslaSupercharger": None,
    'evCharger': None,
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
        if store := response.json()['stores']:
            for store in store:
                store['addr_street'] = store.pop('address')
                item = DictParser.parse(store)
                item['ref'] = store.get("storeNumber")
                item['website'] = f'https://orders.sheetz.com/findASheetz/store/{store["storeNumber"]}'
                item['image'] = f'https://orders.sheetz.com{store.get("imageUrl")}'
                self.parse_features(item, store)
                apply_category(Categories.FUEL_STATION, item)
                yield item
            yield self.make_request(response.meta["state"], 1 + response.meta["page"])

    def parse_features(self, item: Feature, store: dict):
        features = store.get('features', {})
        for k, v in features.items():
            if tag := FEATURES_MAPPING.get(k):
                if isinstance(v, bool):
                    apply_yes_no(tag, item, v)
                elif isinstance(v, int):
                    apply_yes_no(f'{tag.value if isinstance(tag, Enum) else tag}={v}', item, True)
            else:
                self.crawler.stats.inc_value(f'atp/sheetz/feature/failed/{k}')
