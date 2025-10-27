from typing import Any, AsyncIterator, Iterable
from urllib.parse import quote

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.costco_ca_gb_us import COSTCO_SHARED_ATTRIBUTES


class CostcoSpider(JSONBlobSpider):
    name = "costco"
    item_attributes = COSTCO_SHARED_ATTRIBUTES
    locations_key = "stores"

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.costco.com.au/rest/v2/australia/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.es/rest/v2/spain/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.is/rest/v2/iceland/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.fr/rest/v2/france/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.co.jp/rest/v2/japan/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.co.kr/rest/v2/korea/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.com.mx/rest/v2/mexico/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.co.nz/rest/v2/newzealand/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.se/rest/v2/sweden/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )
        yield JsonRequest(
            url="https://www.costco.com.tw/rest/v2/taiwan/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999",
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["warehouseCode"]
        item["branch"] = feature["displayName"]
        if isinstance(item.get("state"), dict):
            item["state"] = item.get("state")["name"]
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])

        warehouse = item.deepcopy()

        if feature.get("openingHours"):
            try:
                warehouse["opening_hours"] = self.parse_opening_hours(
                    feature["openingHours"].get("weekDayOpeningList", [])
                )
            except:
                self.logger.error(
                    f'Failed to parse opening hours: {feature["openingHours"].get("weekDayOpeningList", [])}'
                )

        apply_category(Categories.SHOP_WHOLESALE, warehouse)
        yield warehouse

        if not feature.get("availableServices"):
            return

        for service in feature["availableServices"]:
            if service["type"] != "GAS_STATION":
                continue
            fuel_station = item.deepcopy()
            fuel_station["ref"] = fuel_station["ref"] + "_FUEL"

            if feature.get("gasStationHours"):
                try:
                    fuel_station["opening_hours"] = self.parse_opening_hours(
                        feature["gasStationHours"].get("weekDayOpeningList", [])
                    )
                except:
                    self.logger.error(
                        f'Failed to parse opening hours: {feature["gasStationHours"].get("weekDayOpeningList", [])}'
                    )

            if fuel_types := feature.get("gasTypes"):
                fuel_types = [fuel["name"] for fuel in fuel_types]
                apply_yes_no(Fuel.OCTANE_87, fuel_station, "Regular" in fuel_types)
                apply_yes_no(Fuel.OCTANE_89, fuel_station, "レギュラー" in fuel_types)
                apply_yes_no(Fuel.OCTANE_91, fuel_station, "Unleaded 91" in fuel_types)
                apply_yes_no(Fuel.OCTANE_93, fuel_station, "Premium" in fuel_types)
                apply_yes_no(
                    Fuel.OCTANE_95,
                    fuel_station,
                    "Premium 95" in fuel_types or "Blyfri" in fuel_types or "95無鉛" in fuel_types,
                )
                apply_yes_no(Fuel.OCTANE_96, fuel_station, "ハイオク" in fuel_types)
                apply_yes_no(Fuel.OCTANE_98, fuel_station, "Premium 98" in fuel_types or "98無鉛" in fuel_types)
                apply_yes_no(
                    Fuel.DIESEL,
                    fuel_station,
                    "Diesel" in fuel_types
                    or "Premium Diesel" in fuel_types
                    or "柴油" in fuel_types
                    or "ディーゼル" in fuel_types,
                )
                apply_yes_no(Fuel.BIODIESEL, fuel_station, "HVO 100" in fuel_types)
                apply_yes_no(Fuel.KEROSENE, fuel_station, "灯油" in fuel_types)
            apply_category(Categories.FUEL_STATION, fuel_station)
            yield fuel_station
            break

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if rule.get("closed"):
                oh.set_closed(rule["weekDay"])
            else:
                oh.add_range(
                    rule["weekDay"],
                    rule["openingTime"]["formattedHour"],
                    rule["closingTime"]["formattedHour"],
                    "%I:%M %p",
                )
        return oh
