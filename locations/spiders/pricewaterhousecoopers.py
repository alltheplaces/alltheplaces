# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PricewaterhouseCoopersSpider(scrapy.Spider):
    name = "pricewaterhousecoopers"
    item_attributes = { 'brand': "PricewaterhouseCoopers" }
    allowed_domains = []
    start_urls = [
        'https://www.pwc.com/content/pwc/script/gx/en/office-locator/data/offices/offices-data_en-us.json',
    ]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for office in data["offices"]:
            addr_full, city_state, postcode = re.match(r"(.*),\s(.+) (\d{5})",  office["address"].replace('+', ' ')).groups()

            state = office["parentRegion"]["id"].replace('-', ' ').title()
            city = city_state.replace(state, "", 1)

            properties = {
                'name':office["name"],
                'ref': office["id"],
                'addr_full': addr_full.strip(),
                'city': city.strip(),
                'state': state.strip(),
                'postcode': postcode.strip(),
                'country': "US",
                'phone': office["departments"][0]["telephone"],
                'lat': float(office["coords"]["latitude"]),
                'lon': float(office["coords"]["longitude"]),
                'website': "https://www.pwc.com/us/en/about-us/pwc-office-locations.html#/office/{}".format(office["id"])
            }

            yield GeojsonPointItem(**properties)
