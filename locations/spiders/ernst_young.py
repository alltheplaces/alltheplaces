# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ErnstYoungSpider(scrapy.Spider):
    name = "ernst_young"
    allowed_domains = []
    start_urls = [
        'https://www.ey.com/eydff/services/officeLocations.json',
    ]

    def parse_office(self, office):
        properties = {
            'name': office["name"],
            'ref': office["href"].replace('/locations/', ''),
            'addr_full': office["officeAddress"].strip().replace('\r\n', ' '),
            'city': office["officeCity"],
            'postcode': office["officePostalCode"],
            'country': office["officeCountry"],
            'phone': office["officePhoneNumber"],
            'lat': float(office["officeLatitude"]),
            'lon': float(office["officeLongitude"]),
        }
        return properties

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for country in data["countries"]:

            for state in country["states"]:
                state_abbr = state["stateAbbreviation"]
                for city in state["cities"]:
                    for office in city["offices"]:
                        properties = self.parse_office(office)
                        properties["state"] = state_abbr
                        properties["website"] = response.urljoin(office["href"])
                        yield GeojsonPointItem(**properties)

            for city in country["cities"]:

                for office in city["offices"]:
                    properties = self.parse_office(office)
                    properties["website"] = response.urljoin(office["href"])
                    yield GeojsonPointItem(**properties)
