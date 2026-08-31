from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.speedway_us import SpeedwayUSSpider

FUEL_TYPES_MAPPING = {
    "DEF": Fuel.ADBLUE,
    "Diesel": Fuel.DIESEL,
    "E85": Fuel.E85,
    "Kerosene": Fuel.KEROSENE,
    "Kersonse": Fuel.KEROSENE,
    "Mid-grade": Fuel.OCTANE_89,
    "Mid-Grade": Fuel.OCTANE_89,
    "Regular": Fuel.OCTANE_87,
    "Premium": Fuel.OCTANE_91,
}

STRIPES = {"brand": "Stripes", "brand_wikidata": "Q7624135"}


class SevenElevenCAUSSpider(Spider):
    name = "seven_eleven_ca_us"
    api = "https://www.7-eleven.com/api/v5/stores/search"
    search_radius = 100
    max_results = 1000
    searchable_points_files = ["us_centroids_100mile_radius_state.csv", "ca_centroids_100mile_radius.csv"]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.seen_ids: set[int] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations(self.searchable_points_files):
            yield JsonRequest(
                url=self.api,
                data={"token": "", "lat": lat, "lon": lon, "radius": self.search_radius, "limit": self.max_results},
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["results"]:
            if location["id"] in self.seen_ids:
                continue
            self.seen_ids.add(location["id"])

            item = DictParser.parse(location)
            item["name"] = None
            item["street_address"] = item.pop("addr_full")
            item["website"] = location.get("seo_web_url")

            hours = location.get("hours") or {}
            if hours.get("message") == "Open 24/7":
                item["opening_hours"] = "24/7"
            elif rules := hours.get("operating"):
                item["opening_hours"] = OpeningHours()
                for rule in rules:
                    item["opening_hours"].add_ranges_from_string("{} {}".format(rule["key"], rule["detail"]))

            apply_yes_no(Extras.ATM, item, "ATM" in location.get("features_display", []))
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in location.get("features_display", []))
            apply_yes_no(Extras.WIFI, item, "Wi-Fi" in location.get("features_display", []))

            brand = location.get("brand_info") or {}
            shop = item.deepcopy()
            shop["ref"] = "{}_SHOP".format(shop["ref"])
            if brand.get("title") == "stripes":
                shop.update(STRIPES)
            elif brand.get("title") == "7-eleven":
                shop.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
            elif brand.get("title") == "speedway" or location.get("name") == "Speedway Store":
                shop.update(SpeedwayUSSpider.item_attributes)
            else:
                shop.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)

            apply_category(Categories.SHOP_CONVENIENCE, shop)

            yield shop

            if "Fuel" in location.get("features_display", []):
                apply_category(Categories.FUEL_STATION, item)
                self.parse_fuel_types(item, location)

                yield item

    def parse_fuel_types(self, item: Feature, store: dict) -> None:
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in store.get("features_display", []))
        apply_yes_no(Fuel.PROPANE, item, "Propane" in store.get("features_display", []))
        if fuel_data := store.get("fuel_data") or {}:
            if grades := fuel_data.get("grades", []):
                for grade in grades:
                    fuel_name = grade.get("name")
                    if tag := FUEL_TYPES_MAPPING.get(fuel_name):
                        apply_yes_no(tag, item, True)
                    else:
                        self.crawler.stats.inc_value(f"atp/7_11/fuel/failed/{fuel_name}")
