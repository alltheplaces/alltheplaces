import json
import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

STOREFRONTS = {
    "cobs-ca-live.myshopify.com": "ecd008b16986e30af1fa2964c12a9955",
    "cobs-us-live.myshopify.com": "ccbe49c160d1245033d1483b1a2c2c6f",
}

LOCATIONS_QUERY = """
                query getLocations($first: Int!, $after: String) {
                  locations(first: $first, after: $after) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    edges {
                      node {
                        id
                        name
                        address {
                          address1
                          address2
                          city
                          province
                          provinceCode
                          zip
                          country
                          countryCode
                          phone
                          latitude
                          longitude
                          formatted
                        }
                        metafields(identifiers: [
                          {namespace: "amb", key: "public_store_name"},
                          {namespace: "amb", key: "opening_hours"},
                          {namespace: "amb", key: "opening_hours_note"},
                          {namespace: "amb", key: "delivery_service"},
                          {namespace: "amb", key: "public_holiday_special_opening_hours"},
                          {namespace: "amb", key: "temporary_closure"},
                          {namespace: "amb", key: "description"},
                          {namespace: "amb", key: "bakery_operator"},
                          {namespace: "amb", key: "timezone"}
                        ]) {
                          key
                          value
                          type
                        }
                      }
                    }
                  }
                }
            """


class CobsBreadSpider(Spider):
    name = "cobs_bread"
    item_attributes = {"brand": "COBS Bread", "brand_wikidata": "Q116771375"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for domain, token in STOREFRONTS.items():
            yield self.query_locations(domain, token)

    def query_locations(self, domain: str, token: str, after: str | None = None) -> JsonRequest:
        return JsonRequest(
            url=f"https://{domain}/api/2025-10/graphql.json",
            headers={
                "X-Shopify-Storefront-Access-Token": token,
            },
            data={
                "query": LOCATIONS_QUERY,
                "variables": {"first": 250, "after": after},
            },
            callback=self.parse_details,
            cb_kwargs={"domain": domain, "token": token},
        )

    def parse_details(self, response: Response, domain: str, token: str) -> Iterable[Feature | JsonRequest]:
        locations = response.json()["data"]["locations"]
        if locations["pageInfo"]["hasNextPage"]:
            yield self.query_locations(domain, token, locations["pageInfo"]["endCursor"])

        website_root = "https://usa.cobsbread.com" if "-us-" in response.url else "https://www.cobsbread.com"
        for location in locations["edges"]:
            location.update(location.pop("node"))
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item.pop("name")
            item["addr_full"] = merge_address_lines(location["formatted"])

            # Unrequested metafields are returned as null
            metafields = {field["key"]: field["value"] for field in location["metafields"] if field}
            store_name = metafields["public_store_name"]
            item["branch"] = store_name.removesuffix(" Bakery")

            # Shopify page handles drop apostrophes and collapse other punctuation into hyphens
            handle = re.sub(r"[^a-z0-9]+", "-", store_name.replace("'", "").lower())
            item["website"] = f"{website_root}/pages/bakeries/{handle}"

            item["opening_hours"] = OpeningHours()
            for day, times in json.loads(metafields["opening_hours"]).items():
                item["opening_hours"].add_range(day, times["open"], times["close"])
            apply_category(Categories.SHOP_BAKERY, item)
            yield item
