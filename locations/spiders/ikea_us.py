# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS=['Mo','Tu','We','Th','Fr','Sa','Su']

class IkeaUSSpider(scrapy.Spider):
    name = "ikea_us"
    allowed_domains = ["ikea.com"]
    start_urls = (
        'https://ww8.ikea.com/ext/iplugins/en_US/production/editions/sizmecplus/prio.min.js',
    )

    def get_string(self,stri):
        match=re.search(r"(\d{1,2}):(\d{2})(am|pm|PM|AM)\s*(:|-)\s*(\d{1,2}):(\d{2})(am|pm|PM|AM)",stri)
        try:
            res = str(int(match[1])+(12 if match[3] in ['pm','PM'] else 0)) +':'+match[2]+'-'
            res += str(int(match[5])+(12 if match[7] in ['pm','PM'] else 0)) +':'+match[6]
        except Exception as e:
            res = stri        
        return res

    def store_hours(self, store_hours):
        lastday=DAYS[0]
        lasttime=self.get_string(store_hours[0])
        opening_hours=lastday

        for day in range(1,7): #loop by days
            if day==len(store_hours):
                break
            str_curr=self.get_string(store_hours[day])

            if str_curr != lasttime:
                if lastday==DAYS[day-1]:
                    opening_hours+=' '+lasttime+';'+DAYS[day]
                else:
                    opening_hours+='-'+DAYS[day-1]+' '+lasttime+';'+DAYS[day]
                lasttime=str_curr
                lastday=DAYS[day]
        if lasttime != '':
            if lastday==DAYS[day]:
                opening_hours+=' '+str_curr
            else:
                opening_hours+='-'+DAYS[6]+' '+str_curr
        else:
            opening_hours=opening_hours.rstrip(DAYS[6])

        return opening_hours.rstrip(';').strip()

    def parse(self, response): #high-level list of states
        stri = response.text
        begin_st = stri.find('t=[[')+2
        end_st = stri[begin_st:].find(']]')+begin_st+2
        shops = json.loads(stri[begin_st:end_st].replace('"','\\"').replace("\'", '"'))
        for shop in shops:
            address_parts = re.search(r"(.*),\s*(.*)\s*,\s*(\D{2})\s*(\d{5})",shop[1])

            try:
                state = address_parts[3]
            except Exception as e:
                state = ''

            try:
                addess = address_parts[1]
            except Exception as e:
                addess = ''

            try:
                city = address_parts[2]
            except Exception as e:
                city = ''

            try:
                zip_code = address_parts[4]
            except Exception as e:
                zip_code = ''

            yield GeojsonPointItem(
                lat=float(shop[2]),
                lon=float(shop[3]),
                phone=shop[4],
                ref=shop[0],
                opening_hours=self.store_hours(shop[8:15]),
                addr_full=addess,
                city=city,
                state=state,
                postcode=zip_code,
                country='US',
            )
