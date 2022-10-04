# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class CafeZupasSpider(scrapy.Spider):
    name = "cafe_zupas"
    item_attributes = {"brand": "Cafe Zupas"}
    allowed_domains = ["cafezupas.com"]
    start_urls = [
        "https://cafezupas.com/server.php?url=https://api.controlcenter.zupas.com/api/markets/listing"
    ]

    def parse(self, response):
        data = response.json()
        for i in data["data"]["data"]:
            for location in i["locations"]:
                properties = {
                    "ref": "https://cafezupas.com/locationcopy/info/"
                    + location["name"].lower().replace(" ", "-"),
                    "website": "https://cafezupas.com/",
                    "name": location["name"],
                    "image": "https://cafezupas.com" + location["image"]
                    if location["image"] is not None
                    else None,
                    "phone": location["phone"],
                    "lat": location["lat"],
                    "lon": location["long"],
                    "addr_full": location["address"],
                    "city": location["city"],
                    "state": location["state"],
                    "postcode": location["zip"],
                    "facebook": location["facebook_url"],
                    "opening_hours": "Fr-Sa "
                    + location["fri_sat_timings_open"]
                    + "-"
                    + location["fri_sat_timings_close"]
                    + "; Mo-Th "
                    + location["mon_thurs_timings_open"]
                    + "-"
                    + location["mon_thurs_timings_close"]
                    + "; Su "
                    + location["sunday_timings"],
                }
                yield GeojsonPointItem(**properties)
