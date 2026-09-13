import base64
import json
from typing import Any

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class StinkerStoresUSSpider(Spider):
    name = "stinker_stores_us"
    item_attributes = {"brand": "Stinker", "brand_wikidata": "Q95990164", "name": "Stinker"}
    start_urls = ["https://www.stinker.com/_api/v1/access-tokens"]

    def parse(self, response: Any):
        access_tokens = response.json()
        # The Wix Cloud Data API requires the "wixcode-pub." prefixed app instance token.
        app_id, authorization = next(
            (app_id, app["instance"])
            for app_id, app in access_tokens["apps"].items()
            if app["instance"].startswith("wixcode-pub.")
        )
        query = {
            "dataCollectionId": "StoreLocations",
            "query": {"paging": {"limit": 1000}},
            "environment": "LIVE",
            "appId": app_id,
        }
        encoded_query = base64.b64encode(json.dumps(query).encode()).decode()
        yield Request(
            f"https://www.stinker.com/_api/cloud-data/v2/items/query?.r={encoded_query}",
            headers={
                "Cookie": f"svSession={access_tokens['svSession']}; hs={access_tokens['hs']}",
                "authorization": authorization,
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Any):
        for data_item in response.json()["dataItems"]:
            location = data_item["data"]

            # "Stinker HQ" is the brand's head office, not a public retail location.
            if location["_id"] == "3ae2c7cc-26c1-470d-8816-13e762bfc882":
                continue

            address = location["address"]
            item = Feature(
                ref=location["_id"],
                branch=location["title_fld"],
                lat=address["location"]["latitude"],
                lon=address["location"]["longitude"],
                housenumber=address["streetAddress"].get("number"),
                street=address["streetAddress"].get("name"),
                city=address.get("city"),
                state=address.get("subdivision"),
                postcode=address.get("postalCode"),
                country=address.get("country"),
                addr_full=address.get("formatted"),
            )

            apply_category(Categories.SHOP_CONVENIENCE, item)
            apply_category(Categories.FUEL_STATION, item)

            yield item
