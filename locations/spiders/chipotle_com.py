# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class ChipotleSpider(scrapy.Spider):

    name = "chipotle_com"
    allowed_domains = ["www.chipotle.com"]
    start_urls = (
        'https://www.chipotle.com/locations/search?address=San+Francisco&distanceMode=1&region=us&pageIndex=0&countPerPage=100&radius=10000',
    )
    # default_url_front = 'https://www.chipotle.com/locations/search?address=San+Francisco&distanceMode=1&region=us&pageIndex='
    # default_url_back = '&countPerPage=100&radius=10000'
    # for index in range(70):
    #     start_urls = start_urls + (default_url_front + str(index) + default_url_back, )

    def store_hours(self, store_hours):
        opening_hours = ""

        for time_str in store_hours:
            print(time_str)
            time_str = time_str.replace('Mon', 'Mo').replace('Tue', 'Tu').replace('Thu', 'Th').replace('Fri', 'Fr').replace('Sat', 'Sa').replace('Sun', 'Su')
            time_str = time_str.replace('\r', '')
            
            match = re.search(r'(\d{1,}):(\d{1,}) (A|P)M', time_str)
            (f_hr, f_min, f_ampm) = match.groups()
            
            match = re.search(r'- (\d{1,}):(\d{1,}) (A|P)M', time_str)
            (t_hr, t_min, t_ampm) = match.groups()

            if f_ampm == 'p':
                f_hr += 12
            elif f_ampm == 'a' and f_hr == 12:
                f_hr = 0
            # day_hours = day_hours.replace(h + ' PM', str(new_h) + ':00')
            opening_hours += '{}; '.format(day_hours)            
        
        opening_hours = opening_hours[:-1]

        return opening_hours

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results['restaurants']:
            properties = {
                'ref': data['id'],
                'lat': data['latitude'],
                'lon': data['longitude'],
                'addr_full': data['address1'],
                'city': data['city'],
                'state': data['state'],
                'postcode': data['zipcode'],
                'phone': data['phone'],
                'opening_hours': self.store_hours(data['open_close_info']),
                'website': data['order_url']
                }

            yield GeojsonPointItem(**properties)
