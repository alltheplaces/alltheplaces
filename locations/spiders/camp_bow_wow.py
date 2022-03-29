# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CampBowWowSpider(scrapy.Spider):
    name = "camp_bow_wow"
    allowed_domains = ["campbowwow.com"]

    def start_requests(self):
        url = "https://www.campbowwow.com/locations/?CallAjax=GetLocations"

        yield scrapy.http.Request(url, method="POST", callback=self.parse)

    def parse(self, response):
        data = response.json()

        for place in data:
            properties = {
                "ref": place["FranchiseLocationID"],
                "name": place["FranchiseLocationName"],
                "addr_full": place["Address1"],
                "city": place["City"],
                "state": place["State"],
                "postcode": place["ZipCode"],
                "country": place["Country"],
                "lat": place["Latitude"],
                "lon": place["Longitude"],
                "phone": place["Phone"],
            }

            yield GeojsonPointItem(**properties)
