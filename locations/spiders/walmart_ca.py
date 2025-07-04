import json
from typing import Any, Iterable
from urllib.parse import urlencode

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class WalmartCASpider(scrapy.Spider):
    name = "walmart_ca"
    allowed_domains = ["www.walmart.ca"]
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
        "ROBOTSTXT_OBEY": False,
    }
    base_url = "https://www.walmart.ca/orchestra/graphql/nearByNodes"
    hash = "383d44ac5962240870e513c4f53bb3d05a143fd7b19acb32e8a83e39f1ed266c"

    def start_requests(self) -> Iterable[JsonRequest]:
        # Tried raw GraphQL query, but it's blocked, hash appears to be stable and required for successful requests.
        for city in city_locations("CA", min_population=15000):
            variables = {
                "input": {
                    "postalCode": "",
                    "accessTypes": ["PICKUP_INSTORE", "PICKUP_CURBSIDE"],
                    "nodeTypes": ["STORE", "PICKUP_SPOKE", "PICKUP_POPUP"],
                    "latitude": city["latitude"],
                    "longitude": city["longitude"],
                    "radius": 100,
                },
                "checkItemAvailability": False,
                "checkWeeklyReservation": False,
                "enableStoreSelectorMarketplacePickup": False,
                "enableVisionStoreSelector": False,
                "enableStorePagesAndFinderPhase2": False,
                "enableStoreBrandFormat": False,
                "disableNodeAddressPostalCode": False,
            }
            yield JsonRequest(
                url=f"{self.base_url}/{self.hash}?{urlencode({'variables': json.dumps(variables)})}",
                headers={
                    "x-apollo-operation-name": "nearByNodes",
                    "x-o-bu": "WALMART-CA",
                    "x-o-segment": "oaoh",
                },
                cookies={"walmart.nearestLatLng": f'{city["latitude"]},{city["longitude"]}'},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_nodes = response.json().get("data", {}).get("nearByNodes") or {}
        for location in location_nodes.get("nodes", []):
            item = DictParser.parse(location)
            item["branch"] = location.get("displayName", "").split(",")[0].strip()
            item["street_address"] = merge_address_lines(
                [location["address"].get("addressLineOne"), location["address"].get("addressLineTwo")]
            )
            item["opening_hours"] = self.parse_hours(location.get("operationalHours", []))

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item

    def parse_hours(self, hours: list) -> OpeningHours | None:
        if not hours:
            return None

        try:
            oh = OpeningHours()
            for rule in hours:
                if rule.get("closed"):
                    oh.set_closed(rule.get("day"))
                oh.add_range(rule.get("day"), rule.get("start"), rule.get("end"))
            return oh
        except Exception as e:
            self.logger.error(f"Failed to parse hours: {hours}, {e}")
            return None
