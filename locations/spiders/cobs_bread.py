import json
from typing import Any

from requests import Response
from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CobsBreadSpider(Spider):
    name = "cobs_bread"
    item_attributes = {"brand": "COBS Bread", "brand_wikidata": "Q116771375"}
    start_urls = [
        "https://www.cobsbread.com/pages/bakeries/leaside-bakery",
        "https://usa.cobsbread.com/pages/store-locator",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = response.xpath("//@data-storefront-access-token").get()
        domain = response.xpath("//@data-shop-domain").get()
        version = response.xpath("//@data-storefront-api-version").get()
        yield JsonRequest(
            url=f"https://{domain}/api/{version}/graphql.json",
            headers={
                # 'Content-Type': 'application/json',
                "X-Shopify-Storefront-Access-Token": token,
            },
            data={
                "query": """
                query getLocations($first: Int!, $after: String) {
                  locations(first: $first, after: $after) {
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      cursor
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
            """,
                "variables": {"first": 250},
            },
            callback=self.parse_details,
        )

    def parse_details(self, response, **kwargs):
        for location in response.json()["data"]["locations"]["edges"]:
            location.update(location.pop("node"))
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["addr_full"] = ",".join(location["formatted"])
            oh = OpeningHours()
            for details in location["metafields"]:
                if details is not None:
                    if details.get("key") == "public_store_name":
                        item["name"] = details["value"]
                    elif details.get("key") == "opening_hours":
                        opening_hours_data = json.loads(details["value"])
                        for day, time in opening_hours_data.items():
                            open_time = time["open"]
                            close_time = time["close"]
                            if open_time != "null":
                                oh.add_range(day, open_time, close_time)
                    else:
                        continue
            item["opening_hours"] = oh
            if "-us-" in response.url:
                item["website"] = "https://usa.cobsbread.com/pages/bakeries/" + item["name"].replace(" ", "-")
            elif "-ca-" in response.url:
                item["website"] = "https://www.cobsbread.com/pages/bakeries/" + item["name"].replace(" ", "-")
            yield item
