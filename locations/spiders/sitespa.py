# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem

class SiteSPASpider(scrapy.Spider):
    #download_delay = 0.2
    name = "sitespa"
    item_attributes = {'brand': "SITE SpA"}
    allowed_domains = ["sitespa.com"]

    start_urls = [
        'https://www.sitespa.it/sedisite/jm-ajax/get_listings/'
    ]

    def parse(self, response):
        data = response.json()
        for i in data['listings']:
            try:
                city = i['json_ld']['address']['addressLocality']
            except:
                city = ''
            try:
                pc = i['json_ld']['address']["postalCode"],
            except:
                pc = ''
            try:
                country = i['json_ld']['address']["addressCountry"]
            except:
                country = ''
            properties = {
                'ref': i['id'],
                'name': i['title'],
                'addr_full': i['location']['raw'],
                'city': city,
                'postcode': pc,
                'country': country,
                'phone': i['telephone'],
                'lat': i['location']['lat'],
                'lon': i['location']['lng'],
            }

            yield GeojsonPointItem(**properties)
