# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PrimePubsSpider(scrapy.Spider):
    name = "prime_pubs"
    allowed_domains = ["google.com"]
    start_urls = [
        "https://spreadsheets.google.com/feeds/list/1idWVGZkrRLTEkm6eB0baD9J7G6u-4rLIud4BL52Md3Q/1/public/values?alt=json",
    ]

    def parse(self, response):
        places = response.json()

        for place in places["feed"]["entry"]:
            brand = place["gsx$storename"]["$t"]
            if "FIONN MACCOOL'S" in brand:
                brand = "Fionn MaCcool's"
            elif "D'ARCY MCGEE'S" in brand:
                brand = "D'Arcy McGee's"
            elif "PADDY FLAHERTY'S" in brand:
                brand = "Paddy Flaherty's"
            elif "TIR NAN ÓG KINGSTON" in brand:
                brand = "Tir Nan Óg"

            properties = {
                "ref": place["gsx$storenumber"]["$t"],
                "name": place["gsx$storename"]["$t"],
                "addr_full": place["gsx$streetnumber"]["$t"]
                + " "
                + place["gsx$street"]["$t"],
                "city": place["gsx$city"]["$t"],
                "state": place["gsx$province"]["$t"],
                "postcode": place["gsx$postalcode"]["$t"],
                "country": "CA",
                "lat": place["gsx$latitude"]["$t"],
                "lon": place["gsx$longitude"]["$t"],
                "phone": place["gsx$phonenumber"]["$t"],
                "brand": brand,
            }

            yield GeojsonPointItem(**properties)
