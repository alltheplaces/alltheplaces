# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem

class CintasSpider(scrapy.Spider):
    # download_delay of 0.0 results in rate limiting and 403 errors.
    download_delay = 0.2
    name = "cintas"
    item_attributes = {'brand': "Cintas", 'brand_wikidata': "Q1092571"}
    allowed_domains = ["cintas.com"]
    start_urls = (
        'https://www.cintas.com/local/usa',
    )

    def parse(self, response):
        urls = response.xpath('//ul[@class="col-3 group locations"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        facilityurls = response.xpath('//ul[@id="accordion"]//a/@href').extract()
        for facilityurl in facilityurls:
            yield scrapy.Request(response.urljoin(facilityurl), callback=self.parse_store)

    def parse_store(self, response):
        try:
            data = json.loads(response.xpath('//script[@type="application/ld+json" and contains(text(), "addressLocality")]/text()').extract_first())
            store = data['address']['streetAddress'] + ',%20' + data['address']['addressLocality'] + ',%20' + data['address']['addressRegion']
            storeurl= 'https://www.cintas.com/sitefinity/public/services/locationfinder.svc/search/{}/50'.format(store)
            if data['address']['addressLocality'] + ', ' + data['address']['addressRegion'] == 'Missoula, MT':
                pass
            else:
                yield scrapy.Request(response.urljoin(storeurl), callback=self.parse_loc)
        except:
            pass

    def parse_loc(selfself, response):
        global ref, full_address, locality, state, pc, phone, lat, lon
        geocoderdata = response.xpath('//body//text()').extract()
        geocodertext = geocoderdata[0]
        geocodertext = geocodertext.replace('[', '')
        geocode_re = re.search('distance(.*)', geocodertext).group()
        for item in geocode_re.split('location":{'):
            geocode_replace = item.replace('}', '')
            geocode_replace = geocode_replace.replace('{', '')
            geocode_replace = geocode_replace.replace(']', '')
            geocode_replace = geocode_replace.replace("'", '')
            for j in geocode_replace.split(','):
                try:
                    i = j.split(':')
                    if i[0].startswith('"Lati'):
                        lat = float(i[1].replace('"', ''))
                    elif i[0].startswith('"Longit'):
                        lon = float(i[1].replace('"', ''))
                    elif i[0].startswith('"Id'):
                        ref = i[1].replace('"', '')
                    elif i[0].startswith('"Address_1'):
                        full_address = i[1].replace('"', '')
                    elif i[0].startswith('"City'):
                        locality = i[1].replace('"', '')
                    elif i[0].startswith('"District'):
                        state = i[1].replace('"', '')
                    elif i[0].startswith('"Postal'):
                        pc = i[1].replace('"', '')
                    elif i[0].startswith('"Phone'):
                        phone = i[1].replace('"', '')

                    properties = {
                        'ref':   ref,
                        'name': 'Cintas',
                        'addr_full': full_address,
                        'city': locality,
                        'state': state,
                        'postcode': pc,
                        'country': "US",
                        'phone': phone,
                        'lat': lat,
                        'lon': lon,
                    }

                    yield GeojsonPointItem(**properties)
                except:
                    pass
