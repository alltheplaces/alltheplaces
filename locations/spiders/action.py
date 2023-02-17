import json

import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class ActionSpider(scrapy.Spider):
    name = "action"
    item_attributes = {"brand": "Action", "brand_wikidata": "Q2634111"}
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "*/*"}}
    start_urls = [
        "https://www.action.com/api/graphql/?operationName=GetAllStores&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2288dea5f796a93dfca07d438ec8abf640c704eb626a10f68034d903d687321cbe%22%7D%2C%22headers%22%3A%7B%22Accept-Language%22%3A%22fr-BE%22%7D%7D"
    ]

    def parse(self, response, **kwargs):
        for store in response.json().get("data").get("getAllStores"):
            query_params = {
                "operationName": "GetStore",
                "variables": {"branchNumber": store.get("branchNumber")},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "1d7097673467141e6bf473c254649e26ff2fc3d941a2d252175bc6066ce76092",
                    },
                    "headers": {"Accept-Language": store.get("cultureName")},
                },
            }

            variables_json = json.dumps(query_params["variables"])
            extensions_json = json.dumps(query_params["extensions"])

            query_url = f"https://www.action.com/api/graphql/?operationName=GetStore&variables={variables_json}&extensions={extensions_json}"

            yield scrapy.Request(
                url=query_url, callback=self.parse_store, headers={"Accept-Language": store.get("cultureName")}
            )

    def parse_store(self, response):
        store = response.json().get("data").get("getStore")
        if store is None:
            return None
        geoloc = store.get("geoLocation")
        oh = OpeningHours()
        for opening_hour in store.get("openingTimes"):
            oh.add_range(DAYS_FULL[opening_hour.get("dayOfWeek") - 1], opening_hour["opening"], opening_hour["closing"])

        yield Feature(
            {
                "ref": str(store.get("id")),
                "name": store.get("name"),
                "street_address": " ".join(
                    filter(None, [store.get("houseNumber"), store.get("houseNumberAddition"), store.get("street")])
                ),
                "housenumber": store.get("houseNumber"),
                "street": store.get("street"),
                "postcode": store.get("postalCode"),
                "city": store.get("city"),
                "country": store.get("countryCode"),
                "website": f"https://www.action.com{store.get('url')}" if store.get("url") else None,
                "lat": geoloc.get("lat"),
                "lon": geoloc.get("long"),
                "opening_hours": oh,
            }
        )
