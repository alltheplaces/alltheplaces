import base64
import json
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

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

GRAPHQL_QUERY = """query stores(
  $brand: String,
  $lat: String,
  $lon: String,
  $radius: Float,
  $limit: Int,
  $offset: Int,
  $curr_lat: String,
  $curr_lon: String,
  $filters: [String]
) {
  stores(
    brand: $brand,
    lat: $lat,
    lon: $lon,
    radius: $radius,
    limit: $limit,
    offset: $offset,
    curr_lat: $curr_lat,
    curr_lon: $curr_lon,
    filters: $filters
  ) {
    id
    brand_id
    brand { name }
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
"""


class SpeedwayUSSpider(Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 210}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.speedway.com/locations",
            callback=self.parse_cookies,
            meta={
                "zyte_api": {
                    "browserHtml": True,
                    "geolocation": "US",
                    "responseCookies": True,
                },
            },
        )

    def extract_token(self, response: Response) -> str | None:
        for cookie in response.raw_api_response.get("responseCookies", []):
            cookie_str = str(cookie.get("value", ""))
            if match := re.search(r"accessToken%22%3A%22([^%]+)", cookie_str):
                return match.group(1)
        return None

    def parse_cookies(self, response: Response) -> Any:
        if not (token := self.extract_token(response)):
            return

        data = {
            "query": GRAPHQL_QUERY,
            "variables": {
                "brand": "speedway",
                "radius": 2000000,
                "limit": 4000,
                "offset": 0,
                "lat": "36.778261",
                "lon": "-119.4179324",
                "curr_lat": "36.778261",
                "curr_lon": "-119.4179324",
                "filters": [],
            },
        }
        yield Request(
            url="https://apis.7-eleven.com/v5/stores/graphql",
            method="POST",
            callback=self.parse_stores,
            meta={
                "zyte_api": {
                    "httpResponseBody": True,
                    "geolocation": "US",
                    "httpRequestMethod": "POST",
                    "httpRequestBody": base64.b64encode(json.dumps(data).encode()).decode(),
                    "customHttpRequestHeaders": [
                        {"name": "Authorization", "value": f"Bearer {token}"},
                        {"name": "Content-Type", "value": "application/json"},
                        {"name": "Accept", "value": "application/json"},
                    ],
                }
            },
        )

    def parse_stores(self, response: Response) -> Any:
        for store in json.loads(response.body)["data"]["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.speedway.com/"
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
        for day_hours in hours.get("operating", []):
            if day_hours.get("is_open"):
                oh.add_range(day_hours.get("day", "")[:2], day_hours.get("open"), day_hours.get("close"))
        return oh

    def parse_fuel(self, item: Feature, fuel_data: dict | None) -> None:
        if fuel_data:
            for grade in fuel_data.get("grades", []):
                if tag := FUEL_TYPES_MAPPING.get(grade.get("name", "").lower()):
                    apply_yes_no(tag, item, True)

    def parse_services(self, item: Feature, services: list) -> None:
        for service in services:
            if tag := SERVICES_MAPPING.get(service.get("slug", "")):
                apply_yes_no(tag, item, True)
