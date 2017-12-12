# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
DAYS=['Mo','Tu','We','Th','Fr','Sa','Su']

class CarrefourSpider(scrapy.Spider):
    name = "carrefour"
    allowed_domains = ["carrefour.com.ar"]
    start_urls = (
        'https://www.carrefour.com.ar/storelocator/index/',
    )
    
    def store_hours(self, store_hours):
        lastday=DAYS[0]
        lasttime=store_hours[0].split('a')[0].strip()+'-'+store_hours[0].split('a')[1].strip()
        opening_hours=lastday
        for day in range(1,7): #loop by days
            time_parts=store_hours[day].split('a')
            string=time_parts[0].strip()+'-'+time_parts[1].strip()

            if string != lasttime:
                if lastday==DAYS[day-1]:
                    opening_hours+=' '+lasttime+';'+DAYS[day]
                else:
                    opening_hours+='-'+DAYS[day-1]+' '+lasttime+';'+DAYS[day]
                lasttime=string
                lastday=DAYS[day]
        if lastday==DAYS[6]:
            opening_hours+=' '+string
        else:
            opening_hours+='-'+DAYS[6]+' '+string           
        return opening_hours.rstrip(';').strip()

    def phone_normalize(self, phone):
        r=re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response): #high-level list of states
        formdata = {'search[address]':'Argentina 1, B1704DIA Ramos Mejía, Buenos Aires, Argentina','search[geocode]': '-34.6494258,-58.580151' }
        yield scrapy.FormRequest('https://www.carrefour.com.ar/storelocator/index/search/',formdata=formdata,callback=self.parse_shops)

    def parse_shops(self, response): #high-level list of states
        shops=response.xpath('//div[@class="storelocator_item"]')
        for shop in shops:
            address=shop.xpath('./div[@class="moreData"]/div/text()').extract()
            id_num=shop.xpath('./div[@class="id"]/text()').extract_first()
            time_data=response.xpath('//div[@id="store-detail-'+id_num+'"]')
            dates=time_data.xpath('./div[@class="timetable"]//td[@class="hour"]/text()').extract()

            yield GeojsonPointItem(
                lat=float(shop.xpath('./div[@class="geodata"]/@data-lat').extract_first()),
                lon=float(shop.xpath('./div[@class="geodata"]/@data-lng').extract_first()),
                phone=time_data.xpath('./div/div[@class="tel"]/text()').extract_first().strip(),
                website='https://www.carrefour.com.ar/storelocator/index/',
                ref=id_num,
                opening_hours=self.store_hours(dates),
                addr_full=address[0],
                city=address[1],
                state='',
                postcode='',
                country='Argentina',
            )
