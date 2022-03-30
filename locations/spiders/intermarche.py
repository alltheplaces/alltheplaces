# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class IntermarcheSpider(scrapy.Spider):
    name = "intermarche"
    allowed_domains = ["intermarche.com"]

    def start_requests(self):
        url = "https://www.intermarche.com/api/service/pdvs/v4/pdvs/zone?r=10000&lat=43.646715&lon=1.433066&min=10000"

        headers = {"x-red-version": "3", "x-red-device": "red_fo_desktop"}

        yield scrapy.http.FormRequest(
            url=url, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        data = response.json()

        for place in data["resultats"]:
            try:
                phone = place["contacts"][0]["contactValue"]
            except:
                phone = ""

            properties = {
                "ref": place["storeCode"],
                "name": place["modelLabel"],
                "addr_full": place["addresses"][0]["address"],
                "city": place["addresses"][0]["townLabel"],
                "postcode": place["addresses"][0]["postCode"],
                "country": "FR",
                "lat": place["addresses"][0]["latitude"],
                "lon": place["addresses"][0]["longitude"],
                "phone": phone,
            }

            yield GeojsonPointItem(**properties)
