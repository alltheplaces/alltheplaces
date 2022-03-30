# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class NespressoSpider(scrapy.Spider):
    name = "nespresso"
    allowed_domains = ["nespresso.com"]

    def start_requests(self):
        countries = ["US", "CA", "FR", "NL", "GB", "DE", "CH", "IT", "ZA"]

        base_url = "https://www.nespresso.com/storelocator/app/find_poi-v4.php?country={country}&lang=EN"

        for country in countries:
            url = base_url.format(country=country)
            yield scrapy.Request(url, callback=self.parse, meta={"country": country})

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "ref": store["point_of_interest"]["point_of_interest_id"]["id"],
                "name": store["point_of_interest"]["address"]["name"][
                    "company_name_type"
                ]["name"]["name"],
                "addr_full": store["point_of_interest"]["address"]["address_line"],
                "city": store["point_of_interest"]["address"]["city"]["name"],
                "state": "",
                "postcode": store["point_of_interest"]["address"]["postal_code"],
                "country": response.meta["country"],
                "lat": store["position"]["latitude"],
                "lon": store["position"]["longitude"],
                "phone": store["point_of_interest"]["phone"],
            }

            yield GeojsonPointItem(**properties)
