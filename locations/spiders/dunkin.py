# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from urllib.parse import urlencode
import json


class DunkinSpider(scrapy.Spider):
    name = "dunkindonuts"
    brand = "Dunkin'"
    allowed_domains = ["dunkindonuts.com", "mapquestapi.com"]

    def start_requests(self):
        base_url = "https://www.mapquestapi.com/search/v2/radius?"

        params = {
            "key": "Gmjtd|lu6t2luan5%2C72%3Do5-larsq",
            "origin": "",
            "units": "m",
            "maxMatches": "4000",
            "radius": "100",
            "hostedData": "mqap.33454_DunkinDonuts",
            "ambiguities": "ignore"
        }

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(',')
                params.update({"origin": lat + "," + lon})
                yield scrapy.Request(url=base_url + urlencode(params))


    def parse(self, response):
        jdata = json.loads(response.body_as_unicode())

        for i in jdata.get('searchResults',[]):

            properties = {
                'ref': i['key'],
                'country': i['fields']['country'],
                'state': i['fields']['state'],
                'city': i['fields']['city'],
                'lat': i['fields']['mqap_geography']['latLng']['lat'],
                'lon': i['fields']['mqap_geography']['latLng']['lng'],
                'phone': i['fields']['phonenumber'],
                'addr_full': i['fields']['address'],
                'postcode': i['fields']['postal'],


            }

            yield GeojsonPointItem(**properties)
