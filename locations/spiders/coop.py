# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class CoopNorgeSpider(scrapy.Spider):
    # download_delay = .2
    name = "coop"
    item_attributes = {"brand": "Coop Norge"}
    allowed_domains = ["coop.no"]
    start_urls = (
        "https://coop.no/StoreService/StoresByBoundingBox?locationLat=59.91844170471853&locationLon=1.73930000000001&latNw=89.25020758985941&lonNw=9.771129833984386&latSe=9.586675819577664&lonSe=121.707470166015636",
    )

    def parse(self, response):
        data = response.json()
        for i in data:
            properties = {
                "ref": i["StoreId"],
                "name": i["Name"],
                "addr_full": i["Address"],
                "country": "NO",
                "phone": i["Phone"],
                "lat": i["Lat"],
                "lon": i["Lng"],
            }

            yield GeojsonPointItem(**properties)
