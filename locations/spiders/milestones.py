# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MilestonesSpider(scrapy.Spider):
    name = "milestones"
    item_attributes = {"brand": "Milestones"}
    allowed_domains = ["google.com", "milestonesrestaurants.com"]
    start_urls = [
        "https://spreadsheets.google.com/feeds/list/19fw3iY-T80mIHgBGAysKyqq5lqcCWWP9WH74mzEz2to/1/public/values?alt=json",
    ]

    def parse(self, response):
        places = response.json()

        for place in places["feed"]["entry"]:
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
            }

            yield GeojsonPointItem(**properties)
