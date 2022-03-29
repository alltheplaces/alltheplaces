# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem


class BankofHawaiiSpider(scrapy.Spider):
    name = "bankofhawaii"
    item_attributes = {"brand": "Bank of Hawaii"}
    allowed_domains = ["boh.com"]
    start_urls = [
        "https://www.boh.com/locations",
    ]

    def start_requests(self):
        template = (
            "https://www.boh.com/get-locations?lat=21.33&lng=-157.845934&radius=25"
        )

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["locations"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            if len(store_data["type"]) == 1:
                location_type = store_data["type"][0]

            elif len(store_data["type"]) == 2:
                location_type = store_data["type"][0] + " & " + store_data["type"][1]

            else:
                location_type = "Null"

            properties = {
                "ref": store_data["id"],
                "name": store_data["displayName"],
                "addr_full": store_data["address"]["address1"],
                "city": store_data["address"]["city"],
                "state": store_data["address"]["state"],
                "postcode": store_data["address"]["zip"],
                "country": "US",
                "lat": float(store_data["geocode"]["latitude"]),
                "lon": float(store_data["geocode"]["longitude"]),
                "extras": {"location_type": location_type},
            }

            yield GeojsonPointItem(**properties)
