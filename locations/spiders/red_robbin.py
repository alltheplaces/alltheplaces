# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class RedRobbinSpider(scrapy.Spider):

    name = "red_robbin"
    allowed_domains = ["www.redrobin.com"]
    start_urls = (
        'https://www.redrobin.com/static/data.locationddp.json?lat=29.8067386&lng=-91.51919780000003&units=miles&maxresults=1200&maxdistance=5000',
    )

    def store_hours(self, store_hours):
        opening_hours = ""

        for key, day_hours in store_hours.items():
            day_hours = day_hours.replace('Mon', 'Mo').replace('Tue', 'Tu').replace('Thu', 'Th').replace('Fri', 'Fr').replace('Sat', 'Sa').replace('Sun', 'Su')
            day_hours = day_hours.replace('a-', ':00-')
            day_hours = day_hours.replace('Midnight', '12:00')
    
            m = re.search('([0-9]{1,2})(p)', day_hours)
            if m:
                h = m.group(1)
                new_h = int(h) + 12
                day_hours = day_hours.replace(h + 'p', str(new_h) + ':00')
            opening_hours += '{}; '.format(day_hours)            
        
        opening_hours = opening_hours[:-1]

        return opening_hours

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results['locations']:
            properties = {
                'ref': data['store_id'],
                'name': data['restaurant_name'],
                'lat': data['latitude'],
                'lon': data['longitude'],
                'addr_full': data['address'],
                'city': data['city_name'],
                'state': data['state'],
                'postcode': data['zipcode'],
                'country': data['country'],
                'phone': data['phone'],
                'website': data['onlineOrderingURL'],
                "opening_hours": self.store_hours(data['hours'])

            }

            yield GeojsonPointItem(**properties)
