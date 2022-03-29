# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BeefOBradysSpider(scrapy.Spider):
    name = "beef_o_bradys"
    allowed_domains = ["locationstogo.com"]

    start_urls = [
        "https://locationstogo.com/beefs/pinsNearestBeefs.ashx?lat1=32.475&lon1=-96.99&range=5000&fullbar=%25&partyroom=%25&catering=%25&breakfast=%25&onlineordering=%25&delivery=%25&type=zip+code++&term=76065",
    ]

    def parse(self, response):
        data = response.json()

        for place in data:
            properties = {
                "ref": place["storeID"],
                "name": place["title"],
                "addr_full": place["address"],
                "city": place["city"],
                "state": place["state"],
                "postcode": place["zip"],
                "lat": place["lat"],
                "lon": place["lng"],
                "phone": place["phone"],
                "website": "https://www.beefobradys.com/" + place["url"],
            }

            yield GeojsonPointItem(**properties)
