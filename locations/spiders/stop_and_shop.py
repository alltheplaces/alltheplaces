# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class StopAndShopSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "stop_and_shop"
    item_attributes = {"brand": "Stop and Shop"}
    allowed_domains = ["stopandshop.com"]
    start_urls = (
        "https://stopandshop.com/apis/store-locator/locator/v1/stores/STSH?storeType=GROCERY&q=11797&maxDistance=1000000&details=true",
    )

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))
        for i in data.items():
            idata = i
            for j in idata:
                if j == "stores":
                    pass
                else:
                    jdata = json.loads(json.dumps(j))
                    for item in jdata:

                        properties = {
                            "ref": item["storeNo"],
                            "name": item["name"],
                            "addr_full": item["address1"] + item["address2"],
                            "city": item["city"],
                            "state": item["state"],
                            "postcode": item["zip"],
                            "country": "US",
                            "lat": float(item["latitude"]),
                            "lon": float(item["longitude"]),
                        }

                        yield GeojsonPointItem(**properties)
