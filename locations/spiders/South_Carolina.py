# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem

class SCSpider(scrapy.Spider):
    download_delay = 0.2
    name = "south_carolina"
    item_attributes = {'brand': "State of South Carolina", 'brand_wikidata': "Q53709977"}
    allowed_domains = ["sc.gov"]
    start_urls = (
        'https://applications.sc.gov/PortalMapApi/api/Map/GetMapItemsByZipcodeCategoryId',
    )

    def parse(self, response):
        with open('./locations/searchable_points/SC_Zips.csv') as zips:
            next(zips)
            for zip in zips:
                zipurl = 'https://applications.sc.gov/PortalMapApi/api/Map/GetMapItemsByZipcodeCategoryId/{}/1,2,3,4,5,6,7'.format(zip.replace('"', ''))
                yield scrapy.Request(response.urljoin(zipurl), callback=self.parse_zip)

    def parse_zip(self, response):
        replace_list = (']', '[', '}', '"', '\\t')

        zipre = response.xpath('//body//text()').extract()
        print(zipre)
        ziptext = zipre[0]
        ziptext = ziptext.replace(',SC', ', SC')
        for item in replace_list:
            ziptext = ziptext.replace(item, '')

        ziptext2 = ziptext.split('{')
        for i in ziptext2:
            try:
                if i.startswith('Id'):
                    i = i.replace(', ', " ")
                    j = i.split(',')
                    for js in j:
                        properties = {
                            'ref': j[0].split(':')[1],
                            'name': j[1].split(':')[1],
                            'addr_full': j[6].split(':')[1] + ' ' + j[5].split(':')[1],
                            'city': '',
                            'state': '',
                            'postcode': '',
                            'country': 'US',
                            'phone': j[7].split(':')[1],
                            'lat': float(j[2].split(':')[1]),
                            'lon': -abs((float(j[3].split(':')[1]))),
                        }

                        yield GeojsonPointItem(**properties)

            except:
                pass
