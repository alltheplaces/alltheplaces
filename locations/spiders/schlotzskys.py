# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class SchlotzskysSpider(scrapy.Spider):
    name = 'schlotzskys'
    allowed_domains = ['schlotzskys.com']
    start_urls = ['https://www.schlotzskys.com/restaurants/']

    def parse_hours(self, hours):
        hours = hours.split('\t')[6]
        return hours


    def parse_address(self, response):
        addr_1 = str(response.xpath('normalize-space(//div[@class="locations-address"])').extract_first()) 
        addr_2 = str(response.xpath('normalize-space(//div[@class="locations-state-city-zip"])').extract_first())
        full_address = addr_1 + ' ' + addr_2
        city = addr_2.split()[0]
        state = addr_2.split()[1]
        postcode = addr_2.split()[2]
        city_state_post = [city, state, postcode]
        return full_address, city_state_post
        
    
    def parse(self, response):
        urls = response.xpath('//div[@class="col-xs-12 col-sm-6 col-md-4 each-location"]/a/@href')
        for url in urls:
            url = response.urljoin(url.extract().strip())
            yield scrapy.Request(url, callback = self.parse_store)

    def parse_store(self, response):
        store_address, city_state_post = self.parse_address(response)
        city = city_state_post[0]
        state = city_state_post[1]
        postcode = city_state_post[2]
        phone_num = response.xpath('//div[@class="locations-phone-fax"]').extract()
        phone_num = str(phone_num).split('>')[2].split('<')[0]
        website = str(response).split(' ')[1].split('>')[0]
        hours = self.parse_hours(response.xpath('//div[@class="locations-hours-time"]').extract_first())
        properties = {
            "ref": website,
            "phone": phone_num,
            "website": website,
            "opening_hours":hours,
            "addr_full": store_address,
            "city": city,
            "state": state,
            "postcode": postcode,
            }
        
        yield GeojsonPointItem(**properties)
        
        
