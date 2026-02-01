from typing import Any, AsyncIterator, Iterable
from urllib.parse import quote, urljoin

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.costco_ca_gb_us import COSTCO_SHARED_ATTRIBUTES


class CostcoAUSpider(JSONBlobSpider):
    name = "costco_au"
    item_attributes = COSTCO_SHARED_ATTRIBUTES
    allowed_domains = ["www.costco.com.au"]
    locations_key = "stores"
    stores_url = "https://www.costco.com.au/rest/v2/australia/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url=self.stores_url)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["warehouseCode"]
        item["branch"] = feature["displayName"]
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])
        item["website"] = urljoin(response.url, f"/store-finder/{quote(item['branch'])}")

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
