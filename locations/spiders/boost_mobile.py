# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class BoostMobileSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "boost_mobile"
    item_attributes = {"brand": "Boost Mobile", "brand_wikidata": "Q4943790"}
    allowed_domains = ["boostmobile.com", "boostmobile.nearestoutlet.com"]
    start_urls = ("https://www.boostmobile.com/locations.html",)

    def parse(self, response):
        with open("./locations/searchable_points/us_zcta.csv") as zips:
            next(zips)
            for zip in zips:
                row = zip.replace("\n", "").replace('"', "")
                searchurl = "https://boostmobile.nearestoutlet.com/cgi-bin/jsonsearch-cs.pl?showCaseInd=false&brandId=bst&results=50&zipcode={pc}".format(
                    pc=row
                )

                yield scrapy.Request(
                    response.urljoin(searchurl), callback=self.parse_search
                )

    def parse_search(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data["nearestOutletResponse"]["nearestlocationinfolist"][
            "nearestLocationInfo"
        ]:

            if i["storeName"].startswith("Boost Mobile"):
                try:
                    lat = float(i["storeAddress"]["lat"])
                except:
                    lat = ""
                try:
                    lon = float(i["storeAddress"]["long"])
                except:
                    lon = ""

                properties = {
                    "ref": i["id"],
                    "name": i["storeName"],
                    "addr_full": i["storeAddress"]["primaryAddressLine"],
                    "city": i["storeAddress"]["city"],
                    "postcode": i["storeAddress"]["zipCode"],
                    "state": i["storeAddress"]["state"],
                    "country": "US",
                    "phone": i["storePhone"],
                    "lat": lat,
                    "lon": lon,
                }
                yield GeojsonPointItem(**properties)
            else:
                pass
