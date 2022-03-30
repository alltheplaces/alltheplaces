# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class UnderArmourSpider(scrapy.Spider):
    name = "under_armour"
    item_attributes = {"brand": "Under Armour"}
    allowed_domains = ["where2getit.com"]

    def start_requests(self):
        url = "https://hosted.where2getit.com/underarmour/2015/rest/locatorsearch?like=0.8625979438724998&lang=en_US"

        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://hosted.where2getit.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://hosted.where2getit.com/underarmour/2015/index1.html",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36",
        }

        form_data = {
            "request": {
                "appkey": "24358678-428E-11E4-8BC2-2736C403F339",
                "formdata": {
                    "geoip": "false",
                    "dataview": "store_default",
                    "order": "UASPECIALITY, UAOUTLET, AUTHORIZEDDEALER, rank,_distance",
                    "limit": "5000",
                    "geolocs": {
                        "geoloc": [
                            {
                                "addressline": "New York",
                                "country": "US",
                                "latitude": "40.7127753",
                                "longitude": "-74.0059728",
                                "state": "NY",
                                "province": "",
                                "city": "New York",
                                "address1": "",
                                "postalcode": "",
                            }
                        ]
                    },
                    "searchradius": "5000",
                    "where": {
                        "or": {
                            "UASPECIALITY": {"eq": "1"},
                            "UAOUTLET": {"eq": "1"},
                            "AUTHORIZEDDEALER": {"eq": ""},
                        }
                    },
                    "false": "0",
                },
            }
        }

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            body=json.dumps(form_data),
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        data = response.json()

        for store in data["response"]["collection"]:
            properties = {
                "ref": store["clientkey"],
                "name": store["subname"],
                "addr_full": store["address1"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postalcode"],
                "country": store["country"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
                "extras": {"location_type": store["name"]},
            }

            yield GeojsonPointItem(**properties)
