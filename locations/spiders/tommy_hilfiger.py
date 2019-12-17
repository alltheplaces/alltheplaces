# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class TommyHilfigerSpider(scrapy.Spider):
    name = "tommy_hilfiger"
    item_attributes = { 'brand': "Tommy Hilfiger" }
    allowed_domains = ['tommy.com']

    def start_requests(self):
        url = 'https://hosted.where2getit.com/tommyhilfiger/rest/locatorsearch?like=0.11100338339866411'

        headers = {
            'origin': 'https://hosted.where2getit.com',
            'Referer': 'https://hosted.where2getit.com/tommyhilfiger/store-locator.html',
            'content-type': 'application/json'
        }

        current_state = json.dumps(
            {"request": {"appkey": "0B93630E-2675-11E9-A702-7BCC0C70A832",
                         "formdata": {"geoip": "false", "dataview": "store_default", "limit": 3000,
                                      "geolocs": {"geoloc": [
                                          {"addressline": "TX", "country": "US", "latitude": 31.9685988,
                                           "longitude": -99.90181310000003, "state": "TX", "province": "", "city": "",
                                           "address1": "", "postalcode": ""}]},
                                      "searchradius": "5000", "where": {"or": {"icon": {"like": ""}}},
                                      "false": "0"}}})

        yield scrapy.Request(
            url,
            method='POST',
            body=current_state,
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())

        for store in stores["response"]["collection"]:
            properties = {
                'ref': store["uid"],
                'name': store["name"],
                'addr_full': store["address1"],
                'city': store["city"],
                'state': store["state"],
                'postcode': store["postalcode"],
                'country': store["country"],
                'lat': store["latitude"],
                'lon': store["longitude"],
                'phone': store["phone"]
            }

            yield GeojsonPointItem(**properties)
