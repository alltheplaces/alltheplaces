import json
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class WalmartUSSpider(Spider):
    name = "walmart_us"
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    allowed_domains = ["www.walmart.com"]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 10,
        "ROBOTSTXT_OBEY": False,
    }
    base_url = "https://www.walmart.com/orchestra/home/graphql/nearByNodes"
    hash = "383d44ac5962240870e513c4f53bb3d05a143fd7b19acb32e8a83e39f1ed266c"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 94):
            variables = {
                "input": {
                    "postalCode": "",
                    "accessTypes": ["PICKUP_INSTORE", "PICKUP_CURBSIDE"],
                    "nodeTypes": ["STORE", "PICKUP_SPOKE", "PICKUP_POPUP"],
                    "latitude": lat,
                    "longitude": lon,
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
                    "x-o-bu": "WALMART-US",
                    "x-o-gql-query": "query nearByNodes",
                    "x-o-platform": "rweb",
                    "x-o-platform-version": "usweb-1.220.0-ada3f07b1e1f576f89fca794606c73b0cd2ce649-8211424r",
                    "x-o-segment": "oaoh",
                },
                cookies={"walmart.nearestLatLng": f"{lat},{lon}"},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_nodes = response.json().get("data", {}).get("nearByNodes") or {}
        for location in location_nodes.get("nodes", []):
            item = DictParser.parse(location)
            item["branch"] = location.get("displayName", "").split(",")[0].strip()
            item["street_address"] = merge_address_lines(
                [location["address"].get("addressLineOne"), location["address"].get("addressLineTwo")]
            )
            item["website"] = f'https://www.walmart.com/store/{item["ref"]}-{item["city"]}-{item["state"]}'.replace(
                " ", "-"
            )
            item["opening_hours"] = self.parse_hours(location.get("operationalHours", []))

            if location["name"] == "Walmart":
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            elif location["name"] == "Walmart Supercenter":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif item["name"].endswith("Neighborhood Market"):
                item["name"] = "Walmart Neighborhood Market"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif item["name"].endswith("Pharmacy"):
                item["name"] = "Walmart Pharmacy"
                apply_category(Categories.PHARMACY, item)
            else:
                self.logger.error("Unknown store format: {}".format(item["name"]))

            yield item

    def parse_hours(self, hours: list) -> OpeningHours | None:
        if not hours:
            return None

        try:
            oh = OpeningHours()
            for rule in hours:
                if rule.get("closed") is True:
                    oh.set_closed(rule.get("day"))
                else:
                    oh.add_range(rule.get("day"), rule.get("start"), rule.get("end"))
            return oh
        except Exception as e:
            self.logger.error(f"Failed to parse hours: {hours}, {e}")
            return None
