# -*- coding: utf-8 -*-

import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class TheNorthFaceSpider(scrapy.Spider):
    name = "the_north_face"
    item_attributes = {"brand": "The North Face"}
    allowed_domains = ["hosted.where2getit.com"]

    def start_requests(self):
        url = "https://hosted.where2getit.com/northface/2015/rest/locatorsearch?like=0.8704346432892842&lang=en_EN"

        headers = {
            "origin": "https://hosted.where2getit.com",
            "Referer": "https://hosted.where2getit.com/northface/2015/index.html",
            "content-type": "application/json",
        }

        current_state = json.dumps(
            {
                "request": {
                    "appkey": "C1907EFA-14E9-11DF-8215-BBFCBD236D0E",
                    "formdata": {
                        "geoip": "false",
                        "dataview": "store_default",
                        "limit": 1000,
                        "order": "rank, _DISTANCE",
                        "geolocs": {
                            "geoloc": [
                                {
                                    "addressline": "Austin TX 78754",
                                    "country": "US",
                                    "latitude": "",
                                    "longitude": "",
                                }
                            ]
                        },
                        "searchradius": "5000",
                        "where": {
                            "visiblelocations": {"eq": ""},
                            "or": {
                                "northface": {"eq": "1"},
                                "outletstore": {"eq": "1"},
                                "retailstore": {"eq": ""},
                                "summit": {"eq": ""},
                            },
                            "and": {
                                "youth": {"eq": ""},
                                "apparel": {"eq": ""},
                                "footwear": {"eq": ""},
                                "equipment": {"eq": ""},
                                "mt": {"eq": ""},
                                "access_pack": {"eq": ""},
                                "steep_series": {"eq": ""},
                            },
                        },
                        "false": "0",
                    },
                }
            }
        )

        yield scrapy.Request(
            url,
            method="POST",
            body=current_state,
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        stores = response.json()

        for store in stores["response"]["collection"]:
            state = store["state"]
            if state == None:
                state = store["province"]

            properties = {
                "ref": store["clientkey"],
                "name": store["name"],
                "addr_full": store["address1"],
                "city": store["city"],
                "state": state,
                "postcode": store["postalcode"],
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
                "website": store["url"],
            }

            yield GeojsonPointItem(**properties)
