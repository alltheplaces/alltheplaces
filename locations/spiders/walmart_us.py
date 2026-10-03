import json
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

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
        "ROBOTSTXT_OBEY": False,
    }
    base_url = "https://www.walmart.com/orchestra/home/graphql/nearByNodes"
    query_hash = "383d44ac5962240870e513c4f53bb3d05a143fd7b19acb32e8a83e39f1ed266c"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.seen_refs: set[str] = set()

    async def start(self) -> AsyncIterator[FormRequest]:
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
            yield FormRequest(
                url=f"{self.base_url}/{self.query_hash}",
                method="GET",
                formdata={
                    "variables": json.dumps(
                        variables | {"input": variables["input"] | {"latitude": lat, "longitude": lon}}
                    )
                },
                headers=headers,
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        if errors := data.get("errors"):
            self.logger.warning("GraphQL errors in response for %s: %s", response.url, errors)
            return
        location_nodes = data.get("data", {}).get("nearByNodes") or {}
        for location in location_nodes.get("nodes", []):
            ref = str(location.get("id"))
            if ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            item = DictParser.parse(location)
            item["branch"] = location.get("displayName", "").split(",")[0].strip()
            address = location.get("address") or {}
            item["street_address"] = merge_address_lines(
                [address.get("addressLineOne"), address.get("addressLineTwo")]
            )
            item["website"] = f"https://www.walmart.com/store/{item['ref']}-{item['city'].replace(' ', '-')}-{item['state']}"
            item["opening_hours"] = self._parse_hours(location.get("operationalHours", []))

            self._apply_store_type(item, location.get("name", ""))

            yield item

    def _apply_store_type(self, item: dict, store_type: str) -> None:
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

    def _parse_hours(self, hours: list) -> OpeningHours | None:
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
            self.logger.error("Failed to parse hours: %s, %s", hours, e)
            return None
