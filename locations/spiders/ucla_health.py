# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class UclaHealthSpider(scrapy.Spider):
    name = "ucla_health"
    allowed_domains = ["maps.uclahealth.org"]
    start_urls = [
        "https://maps.uclahealth.org/googlemaps/json/clinicdatabase.json",
    ]

    def parse(self, response):
        result = response.json()

        for place in result:
            properties = {
                "ref": place["UID"],
                "name": place["Custom - Internal Name"],
                "addr_full": place["Address1"],
                "city": place["City"],
                "state": "CA",
                "postcode": place["Zip"],
                "country": "US",
                "lat": place["Latitude"],
                "lon": place["Longitude"],
                "phone": place["Phone"],
                "website": place["Website"],
            }

            yield GeojsonPointItem(**properties)
