# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

HEADERS = {
    "Accept": "application/json",
}


class BurgerFiSpider(scrapy.Spider):
    name = "burger_fi"
    item_attributes = {"brand": "Burger Fi"}
    allowed_domains = ["order.burgerfi.com"]
    start_urls = ("https://order.burgerfi.com/api/restaurants",)

    def start_requests(self):
        url = self.start_urls[0]
        yield scrapy.Request(url=url, headers=HEADERS, callback=self.parse)

    def parse(self, response):
        data = response.json()

        for store in data["restaurants"]:
            addr_full = "{}, {}, {} {}".format(
                store["streetaddress"], store["city"], store["state"], store["zip"]
            )
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": addr_full,
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "lon": float(store["longitude"]),
                "lat": float(store["latitude"]),
                "phone": store["telephone"],
            }

            yield GeojsonPointItem(**properties)
