import csv
import json

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class InsomniaCookiesSpider(scrapy.Spider):
    name = "insomnia_cookies"
    item_attributes = {"brand": "Insomnia Cookies", "brand_wikidata": "Q16997024"}
    allowed_domains = ["insomniacookies.com"]

    def start_requests(self):
        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            reader = csv.DictReader(points)
            for line in reader:
                graphql_query = {
                    "operationName": "stores",
                    "query": "query stores($lat: Float, $lng: Float, $externalId: String, $orderTypeId: ID) {\n  storeSearch(data: {lat: $lat, lng: $lng, externalId: $externalId, orderTypeId: $orderTypeId}) {\n    lat\n    lng\n    address {\n      address1\n      city\n      state\n      postcode\n      lat\n      lng\n      __typename\n    }\n    stores {\n      id\n      name\n      address\n      distanceToStore\n      phone\n      storefrontImage\n      lat\n      lng\n      inDeliveryRange\n     status\n      note\n      storeType\n      isPickupOpen\n      isDeliveryOpen\n      hours {\n        type\n        days {\n          day\n          hour\n          __typename\n        }\n        __typename\n      }\n      blurb\n      promotionalText\n      __typename\n    }\n    __typename\n  }\n}\n",
                    "variables": {
                        "externalId": None,
                        "lat": float(line["latitude"]),
                        "lng": float(line["longitude"]),
                    },
                }

                yield scrapy.Request(
                    method="POST",
                    headers={
                        "content-type": "application/json",
                        "referer": "https://insomniacookies.com/",
                    },
                    url="https://api.insomniacookies.com/graphql",
                    body=json.dumps(graphql_query),
                )

    def parse(self, response):
        data = json.loads(response.text)

        for store in data.get("data", {}).get("storeSearch", {}).get("stores", []):
            properties = {
                "ref": store.get("id"),
                "lat": store.get("lat"),
                "lon": store.get("lng"),
                "name": store.get("name"),
                "addr_full": store.get("address"),
                "phone": store.get("phone"),
            }

            yield Feature(**properties)
