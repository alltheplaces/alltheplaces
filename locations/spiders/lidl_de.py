# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {'brand': 'Lidl', 'brand_wikidata': "Q151954"}
    allowed_domains = ['virtualearth.net']
    start_urls = [
        'https://spatial.virtualearth.net/REST/v1/data/ab055fcbaac04ec4bc563e65ffa07097/Filialdaten-SEC/Filialdaten-SEC?$filter=Adresstyp%20Eq%201&$top=250&$format=json&$skip=0&key=AvmZsSXvHn2vR2mEhiF9bQ5yJHzwt2Fa1XNUUJr-lOKims2EKIBYnDvunZ6crsyE&Jsonp=displayResultStores'
    ]
    download_delay = 1

    def parse(self, response):
        data = json.loads(re.search(r'displayResultStores\((.*)\)', response.body_as_unicode()).groups()[0])

        stores = data['d']['results']

        for store in stores:
            properties = {
                'name': store["ShownStoreName"],
                'ref': store["EntityID"],
                'addr_full': store["AddressLine"],
                'city': store["Locality"],
                'postcode': store["PostalCode"],
                'country': store["CountryRegion"],
                'lat': float(store["Latitude"]),
                'lon': float(store["Longitude"]),
            }

            yield GeojsonPointItem(**properties)

        if stores:
            i = int(re.search(r'\$skip=(\d+)&', response.url).groups()[0])
            url_parts = response.url.split('$skip={}'.format(i))
            i += 250
            url = "$skip={}".format(i).join(url_parts)
            yield scrapy.Request(url=url)
