# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

class AnytimeFitnessSpider(scrapy.Spider):
    name = 'anytime_fitness'
    allowed_domains = ['www.anytimefitness.com']

    def start_requests(self):
        url = 'https://www.anytimefitness.com/wp-content/uploads/gyms.json'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        gyms = json.loads(response.body_as_unicode())

        for gym in gyms:
            yield GeojsonPointItem(
                lat = gym['latitude'],
                lon = gym['longitude'],
                addr_full = '{}, {}'.format(gym['content']['address'], gym['content']['address2']),
                city = gym['content']['city'],
                phone = gym['content']['phone'],
                state = gym['content']['state_abbr'],
                postcode = gym['content']['zip'],
                ref = gym['content']['url'],
                country = gym['content']['country']
                )
                
                
    
