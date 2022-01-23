# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class ValeroSpider(scrapy.Spider):
    name = "valero"
    item_attributes = {'brand': "Valero", 'brand_wikidata': 'Q1283291'}
    allowed_domains = ["valeromaps.valero.com"]

    def start_requests(self):
        yield scrapy.FormRequest(
            'https://valeromaps.valero.com/Home/Search?SPHostUrl=https:%2F%2Fwww.valero.com%2Fen-us',
            method='POST',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
            },
            formdata={
                'NEBound_Lat': '90',
                'NEBound_Long': '180',
                'SWBound_Lat': '-90',
                'SWBound_Long': '-180',
                'center_Lat': '0',
                'center_Long': '0'
            }
        )

    def parse(self, response):
        result = json.loads(response.body_as_unicode())
        for store in result['StoreList']:
            details = ', '.join([d['DetailName'] for d in store['Details']])
            yield GeojsonPointItem(
                lon=store['Longitude'],
                lat=store['Latitude'],
                ref=store['UniqueID'],
                name=store['StationName'],
                addr_full=store['Address'],
                phone=store['Phone'],
                opening_hours='24/7' if '24 Hours' in details else None,
                extras={
                    'amenity:fuel': True,
                    'amenity:toilets': 'Restroom' in details or None,
                    'atm': 'ATM' in details,
                    'car_wash': 'Car Wash' in details,
                    'fuel:diesel': 'Diesel' in details or None,
                    'fuel:e85': 'E-85' in details or None,
                }
            )
