# -*- coding: utf-8 -*-
import scrapy
#import json
import re

from locations.items import GeojsonPointItem

DAYS=['Mo','Tu','We','Th','Fr','Sa','Su']

class IkeaUKSpider(scrapy.Spider):
    name = "ikea_uk"
    item_attributes = { 'brand': "Ikea" }
    allowed_domains = ["ikea.com"]
    start_urls = (
        'http://www.ikea.com/gb/en/store/',
    )


    def store_hours(self, store_hours):
        hours={}
        for i in store_hours:
            hours[i[:2]] = i[2:].replace(" ","")

        lastday=DAYS[0]
        lasttime=hours[DAYS[0]]
        opening_hours=lastday

        for day in range(1,7): #loop by days
            if day==len(hours):
                break
            str_curr=hours[DAYS[day]]

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

    def parse(self, response): 
        shops = response.xpath('//div[contains(@class,"ContentBlock__block")]//a/@href')
        for shop in shops:
            yield scrapy.Request(response.urljoin(shop.extract()),callback=self.parse_shops)

    def parse_shops(self, response): 

        store_data = response.xpath('//div[@id="IKEA-PageModule-Store-Store-storecontent"]')
        props = {}
        if store_data:
            props['ref'] = store_data.xpath('.//meta[@itemprop="name"]/@content').extract_first()
            phone = store_data.xpath('.//meta[@itemprop="telephone"]/@content').extract_first().strip()

            if phone:
                props['phone'] = phone
            props['addr_full'] = store_data.xpath('.//meta[@itemprop="streetAddress"]/@content').extract_first()

            if store_data.xpath('.//meta[@itemprop="postalCode"]/@content'):
                props['postcode'] = store_data.xpath('.//meta[@itemprop="postalCode"]/@content').extract_first().strip()

            props['city'] = store_data.xpath('.//meta[@itemprop="addressLocality"]/@content').extract_first()
            props['lat'] = float(store_data.xpath('.//meta[@itemprop="latitude"]/@content').extract_first())
            props['lon'] = float(store_data.xpath('.//meta[@itemprop="longitude"]/@content').extract_first())

            props['country'] = store_data.xpath('.//meta[@itemprop="addressCountry"]/@content').extract_first()

            props['opening_hours'] = self.store_hours(store_data.xpath('.//meta[@itemprop="openingHours"]/@content').extract())
        else:
            props['ref'] = response.xpath('//h1/text()').extract_first()
            hours_parts = response.xpath('//div[contains(.//span/text(),"onday")]/p[1]/span/text()').extract()
            if not hours_parts:
                if response.xpath('//div[contains(./p/text(),"onday")]/p[1]'):
                    hours_parts = response.xpath('//div[contains(./p/text(),"onday")]/p[1]').extract_first().replace("<p>","").replace("</p>","").replace("<br>","").replace("*","").split('\n\t')


            stri=''
            for hours in hours_parts:
                if hours=='' or not hours.find(':0'):
                    continue
                days = hours.replace(' - ','-').replace('*','').split(" ")
                if len(days)!=2:
                    continue
                parts = days[0].split("-")
                for day in parts:
                    stri += day[:2]+"-"
                stri = stri.rstrip("-")+" "+days[1]+";"
            props['opening_hours'] = stri.rstrip(";")
            address = response.xpath('//div[@class="main-body"]/p[contains(.,"ADDRESS:")]').extract_first()
            address = address[address.find("</strong>")+9:]
            address = address[:address.find("<")].strip()
            if address.count(',')==1:
                address_parts = re.search(r"(.*),\s*(.*)\s(.{4})\s(.{3})",address)
            else:
                address_parts = re.search(r"(.*),\s*(.*),\s*(.{4})\s(.{3})",address)
            try:
                props['addr_full'] = address_parts[1]
            except Exception as e:
                props['addr_full'] = address

            try:
                props['city'] = address_parts[2]
            except Exception as e:
                props['city'] = ''
            
            try:
                props['postcode'] = address_parts[3]+' '+address_parts[4]
            except Exception as e:
                props['postcode'] = ''

            props['country'] = 'UK'
        props['website'] = response.url
        yield GeojsonPointItem(**props)
            
