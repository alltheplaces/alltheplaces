from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

FUEL_TYPES_MAPPING = {
    "regular": Fuel.OCTANE_87,
    "mid-grade": Fuel.OCTANE_89,
    "plus": Fuel.OCTANE_89,
    "premium": Fuel.OCTANE_91,
    "diesel": Fuel.DIESEL,
    "e85": Fuel.E85,
    "e-85": Fuel.E85,
    "kerosene": Fuel.KEROSENE,
    "def": Fuel.ADBLUE,
}

SERVICES_MAPPING = {
    "atm": Extras.ATM,
    "car_wash": Extras.CAR_WASH,
    "delivery": Extras.DELIVERY,
    "propane_exchange": Fuel.PROPANE,
}


class SpeedwayUSSpider(Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.speedway.com/api/get-client-token", method="POST", callback=self.parse_token)

    def parse_token(self, response: Response) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://apis.7-eleven.com/v5/stores/graphql",
            data={
                "query": """
                    query stores($brand: String, $lat: String, $lon: String, $radius: Float, $limit: Int) {
                      stores(brand: $brand, lat: $lat, lon: $lon, radius: $radius, limit: $limit) {
                        id
                        hours
                        address
                        city
                        phone
                        state
                        country
                        postal_code
                        lat
                        lon
                        fuel_data
                        services { slug }
                      }
                    }
                """,
                "variables": {
                    "brand": "speedway",
                    "radius": 2000000,
                    "limit": 4000,
                    "lat": "36.778261",
                    "lon": "-119.4179324",
                },
            },
            headers={"Authorization": f"Bearer {response.json()['access_token']}"},
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response) -> Iterable[Feature]:
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["opening_hours"] = self.parse_hours(store.get("hours"))
            self.parse_fuel(item, store.get("fuel_data"))
            self.parse_services(item, store.get("services", []))
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_hours(self, hours: dict | None) -> OpeningHours | str | None:
        if not hours:
            return None
        if hours.get("message") == "Open 24/7":
            return "24/7"
        oh = OpeningHours()
        for day_hours in hours["operating"]:
            if day_hours["detail"] == "12am - 12am":  # Open all day, not closed
                oh.add_range(day_hours["key"][:2], "00:00", "24:00")
            else:
                oh.add_ranges_from_string("{}: {}".format(day_hours["key"], day_hours["detail"]))
        return oh

    def parse_fuel(self, item: Feature, fuel_data: dict | None) -> None:
        if fuel_data:
            for grade in fuel_data.get("grades", []):
                if tag := FUEL_TYPES_MAPPING.get(grade.get("name", "").lower()):
                    apply_yes_no(tag, item, True)

    def parse_services(self, item: Feature, services: list[dict]) -> None:
        for service in services:
            if tag := SERVICES_MAPPING.get(service.get("slug", "")):
                apply_yes_no(tag, item, True)
