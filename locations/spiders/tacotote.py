# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = {
    '&nbsp;':' ',
    'open 24 hrs':'00:00-24:00',
    'monday': 'Mo',
    'tuesday': 'Tu',
    'wednesday': 'We',
    'friday': 'Fr',
    'thursday': 'Th',
    'saturday': 'Sa',
    'sunday': 'Su',
    'open daily':'Mo-Su',
    'mon': 'Mo',
    'sat': 'Sa',
    'thurs': 'Th',
    'sun': 'Su',
    'fri': 'Fr',
    'and':',',
    ' from ':' ',
    'm to ':'m-',
    ' to ':'-',
    '&':',',
    '- ':'-',
    ' -':'-',
    ' :':' ',
    ': ':' ',
    '  ':'',
}

class MisterCarWashSpider(scrapy.Spider):
    name = "tacotote"
    item_attributes = { 'brand': "El Taco Tote" }
    allowed_domains = ["tacotote.com/"]
    start_urls = (
        'http://tacotote.com/site/index.php/en-us/?option=com_storelocator&view=map&format=raw&searchall=1',
    )

    def clear_str (self, str):
        s=str.lower()
        for keys in DAYS:
            s=s.replace(keys,DAYS[keys])
        return s

    def store_hours(self, store_hours):
        if not store_hours or len(store_hours)<5:
            return

        stri = ''
        for line in store_hours.split('<br />'):
            line = self.clear_str(line)

            match = re.search(r'(\w*)(\s*-\s*(\w*))?\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)?\s*-\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)',line)
            
            if not match:
                continue

            stri += match[1][:2]
            
            try:
                stri += match[2][:3]+' '
            except Exception:
                stri += ' '

            if match[5]:
                first_minutes=match[5]
            else:
                first_minutes=':00'

            if match[9]:
                second_minutes=match[9]
            else:
                second_minutes=':00'

            stri += str(int(match[4])+(12 if match[7] in ['pm','mp'] else 0)) +first_minutes+'-'
            stri += str(int(match[8])+(12 if match[10] in ['pm','mp'] else 0)) +second_minutes+';'

        return stri.rstrip(';')

    def parse(self, response):  # high-level list of states
        tacos = response.xpath('//marker')

        for taco in tacos:

            yield GeojsonPointItem(
                lat=float(taco.xpath('.//lat/text()').extract_first()),
                lon=float(taco.xpath('.//lng/text()').extract_first()),
                phone=taco.xpath('.//phone/text()').extract_first(),
                ref=taco.xpath('.//name/text()').extract_first(),
                opening_hours=self.store_hours(taco.xpath('.//fulladdress/text()').extract_first().replace('<p>','').replace('</p>','')),
                addr_full=taco.xpath('.//address/text()').extract_first(),
            )
