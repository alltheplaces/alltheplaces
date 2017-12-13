# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

REPLACES={
    'Store hours:':'',
    '</div><div>':';',
    '<div>':';',
    '</div>':';',
    'PM':'pm',
    'AM':'am',
    'M':'Mo',
    'W':'We',
    'F':'Fr',
    'SAT':'Sa',
    'SUN':'Su',
    'T':'Tu',
    'T':'Th',
    ' ;':';',
    '  ':' ',
}
class HarborFreightSpider(scrapy.Spider):
    name = "harborfreight"
    allowed_domains = ["harborfreight.com"]
    start_urls = (
        'https://www.harborfreight.com/storelocator/location/map',
    )

    def store_hours(self, store_hours):
        if not store_hours or len(store_hours)<5:
            return

        stri = ''
        for line in store_hours.split(';'):
            match = re.search(r'(\D*)\s*(\d{1,2}):(\d{1,2})\s*(am|pm|mp)?\s*-\s*(\d{1,2}):(\d{1,2})\s*(am|pm|mp)\s*(\w*)(\s*-\s*(\w*))?',line)
            stri += match[1].strip()+match[8][:2]

            try:
                stri += match[10][:3]+' '
            except Exception:
                stri += ' '
            stri += str(int(match[2])+(12 if match[4] in ['pm','mp'] else 0)) +':'+match[3]+'-'
            stri += str(int(match[5])+(12 if match[7] in ['pm','mp'] else 0)) +':'+match[6]+';'

        return stri.rstrip(';')

    def phone_normalize(self, phone):
        r=re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response): #high-level list of states
        states=response.xpath('//dl[@id="imap"]//a/@id')
        for state in states:
            yield scrapy.Request('https://www.harborfreight.com/storelocator/location/state?state='+state.extract()+'&justState=true', callback=self.parse_state)

    def parse_state(self, response): #high-level list of cities
        shops=response.xpath('//markers/marker')
        if not shops:
            return
        for shop in shops:
            hours=shop.xpath('.//@notes').extract_first()
            for key in REPLACES:
                hours=hours.replace(key,REPLACES[key])
            hours=hours.strip().strip(';')
            
        yield GeojsonPointItem(
            lat=float(shop.xpath('.//@latitude').extract_first()),
            lon=float(shop.xpath('.//@longitude').extract_first()),
            phone=self.phone_normalize(shop.xpath('.//@phone').extract_first()),
#            website=, no links to shops
            ref=shop.xpath('.//@title').extract_first(),
            opening_hours=self.store_hours(hours),
            addr_full=shop.xpath('.//@address').extract_first(),
            city=shop.xpath('.//@city').extract_first(),
            state=shop.xpath('.//@state').extract_first(),
            postcode=shop.xpath('.//@zip').extract_first(),
            country='USA',
        )
