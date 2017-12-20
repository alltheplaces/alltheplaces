# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class GreatclipsSpider(scrapy.Spider):
    name = "greatclips"
    allowed_domains = ["greatclips.com","stylewaretouch.net",""]
    start_urls = (
        'https://www.stylewaretouch.net/checkin/wa/jsonMarkers?client=locator&lat=-34&lng=85&tzoffset=200&callback=onSuccess&failureCallback=onFailure&stores=',
    )

    def store_hours(self, store_hours):
        if not store_hours or len(store_hours)<5:
            return

        stri = ''
        match = re.search(r'(\d{1,2})(:(\d{1,2}))?\s*(am|AM|mp|PM|pm)?\s*-\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp|PM|AM)',store_hours)
        
        if not match:
            return store_hours

        stri += str(int(match[1])+(12 if match[4] in ['pm','mp','PM'] else 0)) +match[2]+'-'
        stri += str(int(match[5])+(12 if match[8] in ['pm','mp','PM'] else 0)) +match[6]+';'

        return stri.rstrip(';')

    def parse(self, response):
        for i in range(1,10000): #all shops grouped in ther database by codes experimentally was uncovered all groups lies in 1..10000 range (checked till 100000) 
            yield scrapy.Request(
                self.start_urls[0]+str(i),
                callback=self.parse_shop,
                meta={'pos':str(i)}
            )

    def parse_shop(self, response):
        if response.text.find('onFailure')!=-1:
            return
        shops=json.loads(response.text.lstrip('onSuccess(').rstrip(')'))
        if not len(shops):
            return
        for shop in shops:
            props = {}

            props['ref'] = shop['name']
            props['phone'] = shop['phone']
            props['addr_full'] = shop['Thoroughfare']
            props['postcode'] = shop['ZIP']
            props['state'] = shop['State']
            props['city'] = shop['City']
            props['lat'] = float(shop['latitude'])
            props['lon'] = float(shop['longitude'])
            props['website'] = 'https://www.greatclips.com/salons/'+shop['number']
            props['country'] = shop['CountryCode']

            props['opening_hours'] = 'Mo-Fr '+self.store_hours(shop['hours_mon'])+';Sa '+self.store_hours(shop['hours_sat'])+';Su '+self.store_hours(shop['hours_sun'])


            

            yield GeojsonPointItem(**props)
