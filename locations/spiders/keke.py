# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class KekeSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "keke"
    item_attributes = {"brand": "Keke's Breakfast Cafe"}
    allowed_domains = ["storepoint.co"]
    start_urls = ("https://api.storepoint.co/v1/158d5359b0129d/locations?rq",)

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))
        for i in data["results"]["locations"]:

            if i["streetaddress"].split(", ")[-1] == "USA":
                if len(i["streetaddress"].split(", ")) == 4:
                    properties = {
                        "ref": i["id"],
                        "name": i["name"],
                        "addr_full": i["streetaddress"].split(", ")[0],
                        "housenumber": "",
                        "city": i["streetaddress"].split(", ")[1],
                        "state": i["streetaddress"].split(", ")[2].split(" ")[0],
                        "postcode": i["streetaddress"].split(", ")[2].split(" ")[1],
                        "country": "US",
                        "phone": i["phone"],
                        "lat": float(i["loc_lat"]),
                        "lon": float(i["loc_long"]),
                    }
                    yield GeojsonPointItem(**properties)
                elif len(i["streetaddress"].split(", ")) == 5:
                    properties = {
                        "ref": i["id"],
                        "name": i["name"],
                        "addr_full": i["streetaddress"].split(", ")[0],
                        "housenumber": i["streetaddress"].split(", ")[1],
                        "city": i["streetaddress"].split(", ")[2],
                        "state": i["streetaddress"].split(", ")[3].split(" ")[0],
                        "postcode": i["streetaddress"].split(", ")[3].split(" ")[1],
                        "country": "US",
                        "phone": i["phone"],
                        "lat": float(i["loc_lat"]),
                        "lon": float(i["loc_long"]),
                    }
                    yield GeojsonPointItem(**properties)
            elif i["streetaddress"].split(", ")[-1] != "USA":
                if len(i["streetaddress"].split(", ")) == 3:
                    properties = {
                        "ref": i["id"],
                        "name": i["name"],
                        "addr_full": i["streetaddress"].split(", ")[0],
                        "housenumber": "",
                        "city": i["streetaddress"].split(", ")[1],
                        "state": i["streetaddress"].split(", ")[2].split(" ")[0],
                        "postcode": i["streetaddress"].split(", ")[2].split(" ")[1],
                        "country": "US",
                        "phone": i["phone"],
                        "lat": float(i["loc_lat"]),
                        "lon": float(i["loc_long"]),
                    }
                    yield GeojsonPointItem(**properties)
                elif len(i["streetaddress"].split(", ")) == 4:
                    properties = {
                        "ref": i["id"],
                        "name": i["name"],
                        "addr_full": i["streetaddress"].split(", ")[0],
                        "housenumber": i["streetaddress"].split(", ")[1],
                        "city": i["streetaddress"].split(", ")[2],
                        "state": i["streetaddress"].split(", ")[3].split(" ")[0],
                        "postcode": i["streetaddress"].split(", ")[3].split(" ")[1],
                        "country": "US",
                        "phone": i["phone"],
                        "lat": float(i["loc_lat"]),
                        "lon": float(i["loc_long"]),
                    }
                    yield GeojsonPointItem(**properties)
