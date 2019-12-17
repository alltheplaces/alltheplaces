# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class FrysElectronisSpider(scrapy.Spider):
    name = 'frys-electronics'
    chain_name = "Fry's Electronics"
    allowed_domains = ['www.frys.com']
    start_urls = (
        'https://www.frys.com/ac/storeinfo/storelocator',
    )

    def parse_store(self, response):
        address_lines = response.xpath('//div[@id="rightside"]/div[@id="text3"]/div[@id="address"]//b/text()').extract()
        address = ', '.join([ a.strip() for a in address_lines ])
        phone = [ t for t in response.xpath('//div[@id="rightside"]/div[@id="text3"]/div[@id="address"]//text()').extract() if 'Phone' in t ]
        coordinates = [ c for c in response.xpath('//div[@id="rightside"]/div[@id="text3"]/div[@id="maps"]/text()').extract() if '°' in c ]

        properties = {
          'addr_full': address,
          'website': response.url,
          'ref': response.url.split('/')[-1],
        }

        if len(phone) == 1:
            properties['phone'] = phone[0].replace('Phone', '').strip().replace('(', '').replace(') ', '-')
        
        # Try to parse the degree, minutes, seconds coordinate pair
        if coordinates and len(coordinates) == 1:
            # Add a comma to separate lat and lon
            if '" -' in coordinates[0]:
                coordinates[0] = coordinates[0].replace('" -', '", -')
            latlon = coordinates[0].split(',')
            properties['lat'] = self.dms2dd(latlon[0])
            properties['lon'] = self.dms2dd(latlon[1])
        else:
            # Fall back to the ll URL param in the google maps URL
            mapsLink = response.xpath('//div[@id="rightside"]/div[@id="text3"]/div[@id="maps"]/a/@href').extract_first()
            if 'll=' in mapsLink:
                latlon = mapsLink.split('ll=')[1].split('&')[0].split(',')
                properties['lat'] = float(latlon[0])
                properties['lon'] = float(latlon[1])

        yield GeojsonPointItem(**properties)
    
    def dms2dd(self, dms):
        sign = 1
        if '-' in dms or 'W' in dms:
            sign = -1
        degrees = [ d.strip() for d in dms.split('°') ]
        d = int(degrees[0].replace('+', '').replace('-', '').replace('N', '').replace('W', ''))
        minutes = degrees[1].split("'")
        if '.' in minutes[0]:
            m = float(minutes[0]) / 60
            s = 0
        else:
            m = float(minutes[0]) / 60
            s = float(minutes[1].replace('"', '').strip()) / 3600
        dd = (d + m + s) * sign
        return dd

    def parse(self, response):
        urls = response.xpath('//div[@id="main-stores"]//table//a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
