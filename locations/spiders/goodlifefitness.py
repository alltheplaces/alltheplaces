# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class GoodLifeFitnessSpider(scrapy.Spider):
    name = "goodlifefitness"
    item_attributes = {"brand": "GoodLife Fitness"}
    allowed_domains = ["www.goodlifefitness.com"]
    start_urls = ("https://www.goodlifefitness.com/locations",)

    def start_requests(self):
        template = "https://www.goodlifefitness.com/api/club/filterclubsforcitypage"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        store_data = response.json()
        for store in store_data:
            properties = {
                "ref": store["ClubNo"],
                "name": store["ClubName"],
                "addr_full": store["Address1"],
                "city": store["City"],
                "state": store["Province"],
                "postcode": store["PostalCode"],
                "phone": store["Phone"],
                "lat": float(store["Lat"]),
                "lon": float(store["Long"]),
            }

            yield GeojsonPointItem(**properties)
