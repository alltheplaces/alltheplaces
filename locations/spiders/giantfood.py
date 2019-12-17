# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']


class GiantFoodSpider(scrapy.Spider):
    name = "giantfood"
    brand = "Giant Food"
    allowed_domains = ["giantfood.com"]

    def start_requests(self):
        yield scrapy.http.Request(
            'https://giantfood.com/auth/oauth/token',
            callback=self.handle_oauth_token,
            body='grant_type=client_credentials&scope=profile',
            method='POST',
            headers={
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Basic NzJkNTBhZDctNjk4MC00OTQxLWFiNGQtNThkYzM0NjVmMDY5OjczMGUyNzgwMDMxNTkwNWMwYThiYzE0ODRmYTUzM2I2NWM0YWI5Mjc4NzdjZTdiZDYyMzUxODcwMWQ0MDY1ODA=',
            }
        )

    def handle_oauth_token(self, response):
        result = json.loads(response.body_as_unicode())
        access_token = result.get('access_token')

        url = 'https://giantfood.com/auth/api/public/synergy/locator/GNTL/locate/grocery/15/details/'
        headers = {
            'authorization': 'Bearer ' + access_token
        }
        for state in STATES:
            yield scrapy.http.Request(
                '{}?q={}'.format(url, state),
                self.parse,
                method='GET',
                headers=headers
            )

    def parse(self, response):
        result = json.loads(response.body_as_unicode())
        for store in result['stores']:
            ref             = store['storeId']
            name            = 'Giant'
            website         = 'https://giantfood.com/location-details/#/store/detail/' + store['storeNo']
            street          = '{} {}'.format(store['address1'], store['address2'])
            city            = store['city']
            state           = store['state']
            postcode        = store['zip']
            lat             = store['latitude']
            lon             = store['longitude']
            phone           = store['details']['departments'][0]['phone']
            opening_hours   = self.hours(store['details']['departments'][0]['storeDeptHours'])

            properties = {
                'ref'           : ref,
                'name'          : name,
                'website'       : website,
                'lat'           : lat,
                'lon'           : lon,
                'website'       : website,
                'phone'         : phone,
                'opening_hours' : opening_hours,
                'street'        : street,
                'city'          : city,
                'state'         : state,
                'postcode'      : postcode
            }

            yield GeojsonPointItem(**properties)

    def hours(self, store_hours):
        hours = ''
        for data in store_hours:
            if data['24hr']:
                open_time = '00:00'
                close_time = '24:00'
            if 'openTime' in data.keys():
                open_time = data['openTime']
            elif 'pickupStartTime' in data.keys():
                open_time = data['pickupStartTime']
            else:
                open_time = '00:00'

            if 'closeTime' in data.keys():
                close_time = data['closeTime']
            elif 'pickupEndTime' in data.keys():
                close_time = data['pickupEndTime']
            else:
                close_time = '24:00'

            hours = hours + '{} {}-{}; '.format(
                WEEKDAYS[data['day'] - 1],
                open_time,
                close_time
            )

        return hours
