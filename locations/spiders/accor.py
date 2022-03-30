# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class AccorSpider(scrapy.Spider):
    name = "accor"
    allowed_domains = ["accor.com"]
    start_urls = (
        "https://group.accor.com/en/hotel-development/-/Media/Corporate/Master-Page/Maps/Business-Developers-map/accorB2BMap_en.json",
    )

    def parse(self, response):
        data = response.json()

        for i in data["poi"]:
            post = str(i["zipCode"])
            postal = post.zfill(5)

            properties = {
                "ref": i["_id"],
                "name": i["name"],
                "brand": i["brand"],
                "addr_full": i["address"],
                "city": i["city"],
                "postcode": postal,
                "country": i["countryId"],
                "lat": float(i["lat"]),
                "lon": float(i["lng"]),
            }

            yield GeojsonPointItem(**properties)
