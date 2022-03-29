# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class kruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat"}
    allowed_domains = ["kruidvat.nl"]
    start_urls = ("https://www.kruidvat.nl/winkelzoeker",)

    def start_requests(self):
        template = "https://www.kruidvat.nl/api/v2/kvn/stores?lang=nl&radius=100000&pageSize=10000&fields=FULL"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        data = response.json()
        for store_data in data["stores"]:
            stores = json.dumps(store_data)
            store = json.loads(stores)
            properties = {
                "name": store["name"],
                "ref": store["address"]["formattedAddress"],
                "addr_full": store["address"]["line1"],
                "city": store["address"]["town"],
                "state": store["address"].get("province"),
                "postcode": store["address"]["postalCode"],
                "country": store["address"]["region"]["countryIso"],
                "lat": float(store["geoPoint"]["latitude"]),
                "lon": float(store["geoPoint"]["longitude"]),
                "website": "https://www.kruidvat.nl" + store.get("url"),
            }

            yield GeojsonPointItem(**properties)
