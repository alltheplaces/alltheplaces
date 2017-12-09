# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
ALLOWED_ZIPS=[range(500,9899),range(10000,21299),range(21400,26899),range(27000,34299),range(21400,26899),range(27000,34299),
            range(34400,34499),range(34600,34799),range(34900,35299),range(35400,41899),range(42000,42799),range(43000,51699),
            range(52000,52899),range(53000,53299),range(53400,53599),range(53700,55199),range(55300,56799),range(56900,57799),
            range(58000,58899),range(59000,62099),range(62200,63199),range(63300,64199),range(64400,65899),range(66000,66299),
            range(66400,68199),range(68300,69399),range(70000,70199),range(70300,70899),range(71000,71499),range(71600,73199),
            range(73400,74199),range(74300,77099),range(77200,81699),range(82000,83899),range(84000,84799),range(85000,85399),
            range(85500,85799),range(85900,86099),range(86300,86599),range(87000,87199),range(87300,87599),range(87700,88599),
            range(88900,89199),range(89300,89599),range(89700,89899),range(90000,90899),range(91000,92899),range(93000,93799),
            range(93900,96199),range(96700,98699),range(98800,99999)]

class DominosPizzaSpider(scrapy.Spider):
    name = "dominos_pizza"
    allowed_domains = ["dominos.com","google.com"]
    start_urls = (
        'https://order.dominos.com/power/store-locator?type=Carryout&c=00500&s=',
    )

    def store_hours(self, store_hours):
        opening_hours=''
        for s in store_hours.split('\n'): #loop by days
            parts=s.split(' ') # split to days and time period
            time=parts[1].split('-') #split time to begin and end
            if not time:
                continue
            if 'pm' in time[0]:
                time_parts=time[0].replace('pm','').split(':')
                if not time_parts:
                    continue
                hours='{:02d}'.format(int(time_parts[0])+12)+':'+time_parts[1]
            else:
                time_parts=time[0].replace('am','').split(':')
                if not time_parts:
                    continue
                hours='{:02d}'.format(int(time_parts[0]))+':'+time_parts[1]

            opening_hours+=parts[0]+' '+hours+';'
        return opening_hours

    def phone_normalize(self, phone):
        r=re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response): #high-level list of states
        for range_zip in ALLOWED_ZIPS:
            for current_zip in range_zip:
                yield scrapy.Request('https://order.dominos.com/power/store-locator?type=Carryout&c='+'{:05d}'.format(current_zip), callback=self.check_zip)

    def check_zip(self, response):
        json_answer=json.loads(response.body_as_unicode())
        for store in json_answer['Stores']:
            address=re.search(r'(.+)\s*\n\s*(.+)\s*,\s*(\w{2}|N\.Y\.|.{2})\s*(\d{5}).*',store['AddressDescription'])
            if not address:
                address=re.search(r'(.+)\s*\n\s*(.+)\s*,\s*(\w{2}|N\.Y\.|.{2}).*',store['AddressDescription'])
            try:
                zip_str=address[4]
            except Exception as e:
                zip_str=''

            try:
                hours_str=self.store_hours(store['HoursDescription'])
            except Exception as e:
                hours_str=''

            try:
                addr_str=address[1]
            except Exception as e:
                addr_str=store['AddressDescription']

            yield GeojsonPointItem(
    #            lat=float(latlon[0]), no information on site
    #            lon=float(latlon[1]),
                phone=store['Phone'],
                website='https://www.dominos.com/en/pages/order/#/locations/search/',
                ref=store['StoreID'],
                opening_hours=hours_str,
                addr_full=addr_str,
                city=address[2],
                state=address[3],
                postcode=zip_str,
                country='US',
            )
