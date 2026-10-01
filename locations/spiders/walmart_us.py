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
from locations.user_agents import CHROME_LATEST


class WalmartUSSpider(Spider):
    name = "walmart_us"
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    allowed_domains = ["www.walmart.com"]
    custom_settings = {
        "USER_AGENT": CHROME_LATEST,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
    }
    base_url = "https://www.walmart.com/orchestra/home/graphql/nearByNodes"
    hash = "383d44ac5962240870e513c4f53bb3d05a143fd7b19acb32e8a83e39f1ed266c"

    async def start(self) -> AsyncIterator[JsonRequest]:
        headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://www.walmart.com/store-finder",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-apollo-operation-name": "nearByNodes",
            "x-o-bu": "WALMART-US",
            "x-o-gql-query": "query nearByNodes",
            "x-o-mart": "B2C",
            "x-o-platform": "rweb",
            "x-o-platform-version": "usweb-1.220.0-ada3f07b1e1f576f89fca794606c73b0cd2ce649-8211424r",
            "x-o-segment": "oaoh",
        }
        variables = {
            "input": {
                "postalCode": "",
                "accessTypes": ["PICKUP_INSTORE", "PICKUP_CURBSIDE"],
                "nodeTypes": ["STORE"],
                "latitude": 0.0,
                "longitude": 0.0,
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

        for lat, lon in country_iseadgg_centroids("US", 94):
            variables["input"]["latitude"] = lat
            variables["input"]["longitude"] = lon
            yield JsonRequest(
                url=f"{self.base_url}/{self.hash}?{urlencode({'variables': json.dumps(variables)})}",
                headers=headers,
            )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.seen_refs: set[str] = set()

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_nodes = response.json().get("data", {}).get("nearByNodes") or {}
        for location in location_nodes.get("nodes", []):
            ref = str(location.get("id"))
            if ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            item = DictParser.parse(location)
            if geo_point := location.get("geoPoint"):
                item["lat"] = geo_point.get("latitude")
                item["lon"] = geo_point.get("longitude")
            item["branch"] = location.get("displayName", "").split(",")[0].strip()
            item["street_address"] = merge_address_lines(
                [location["address"].get("addressLineOne"), location["address"].get("addressLineTwo")]
            )
            item["website"] = f'https://www.walmart.com/store/{item["ref"]}-{item["city"]}-{item["state"]}'.replace(
                " ", "-"
            )
            item["opening_hours"] = self.parse_hours(location.get("operationalHours", []))

            store_type = location.get("name", "")
            if store_type == "Walmart Supercenter":
                item["name"] = "Walmart Supercenter"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif "Neighborhood Market" in store_type:
                item["name"] = "Walmart Neighborhood Market"
                item["brand"] = "Walmart Neighborhood Market"
                item["brand_wikidata"] = "Q7963529"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif "Pharmacy" in store_type:
                item["name"] = "Walmart Pharmacy"
                apply_category(Categories.PHARMACY, item)
            else:
                item["name"] = "Walmart"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item

    def parse_hours(self, hours: list) -> OpeningHours | None:
        if not hours:
            return None

        try:
            oh = OpeningHours()
            for rule in hours:
                day = rule.get("day")
                if rule.get("closed") is True:
                    oh.set_closed(day)
                else:
                    oh.add_range(day, rule.get("start"), rule.get("end"))
            return oh
        except Exception as e:
            self.logger.error(f"Failed to parse hours: {hours}, {e}")
            return None
