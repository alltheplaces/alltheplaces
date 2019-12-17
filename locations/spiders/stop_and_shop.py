#https://stopandshop.com/auth/api/public/synergy/locator/SNS/locate/grocery/15/details/?q=ny&_=1513540843051
# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

class StopAndShopSpider(scrapy.Spider):
    """ Spider to scrape Stop and Shop locations """
    name = "stop_and_shop"
    item_attributes = { 'brand': "Stop and Shop" }
    allowed_domains = ["stopandshop.com"]

    def start_requests(self):
        """ Initial requests. Gets the authorization token via a POST request """
        yield scrapy.Request('https://stopandshop.com/auth/oauth/token',
                             callback=self.handle_oauth_token,
                             body='grant_type=client_credentials&scope=profile',
                             method='POST',
                             headers = {'referer': 'https://stopandshop.com/store-locator',
                                        'content-type': 'application/x-www-form-urlencoded',
                                        'Authorization': 'Basic NTRhOGMwMTItOTk1Ni00NGE1LTk2MWItMjBmOTM1MjFjMTVlOjczNzk3ZTQ3YmRhMGQ5NzQ3ZjlmOGI2NTg5YTc2YzgzNjhjODI3ZmRkNjU0YmFhNjQ5MjYwZWY0OGI0MmM1YTY=',
                                        'cookie': "__cfduid=d9a7b3d594509b93a7a1ed9aa246872e71513750458; v1st=31F5C8721F42B4EF; JSESSIONID=2C1kh51hT7Ln18p4G9JLs7GZsSxpTC2Q23slv1cgn3SSLTg2zHnj!-1912720414; _vwo_uuid_v2=F771B1EED04A63F5EF42E2AD70E2BA8B|d16dd67896b01fcaa9bb6e7b6a96c74d; OAUTH_access_token=3698d5f3b378ec4f5553df2c7d0a6888428b93efdc16caf7cd425b053aa42a3e"})

    def handle_oauth_token(self, response):
        """ Makes requests for each state. Puts the auth token in the headers for each request. Callback for start_requests() """
        result = json.loads(response.body_as_unicode())
        access_token = result.get('access_token')

        url = 'https://stopandshop.com/store-locator'
        search_url = 'https://stopandshop.com/auth/api/public/synergy/locator/SNS/locate/grocery/15/details/?q={}&_=1513548548773'

        headers = {'authorization': ''.join(['Bearer', access_token]),
                   'referer': url,
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
                   'X-Requested-With': 'XMLHttpRequest'
        }

        for state in STATES: 
            state_url = search_url.format(state)
            yield scrapy.Request(state_url,
                                 dont_filter=True,
                                 callback=self.parse,
                                 method='GET',
                                 headers=headers)
            
    def parse(self, response):
        """ Extracts data and yields GeojsonPointItems. Callback for handle_oauth_token() """
        if response.url == 'https://stopandshop.com/store-locator/': # States with no stores get redirected to this page 
           return 

        stores = json.loads(response.body_as_unicode())

        for store in stores['stores']:
            properties = {
                'ref': store['storeNo'],
                'name': store['name'],
                'addr_full': store['address1'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['zip'],
                'country': 'USA',
                'lon': store['longitude'],
                'lat': store['latitude'],
                'phone': store['details']['departments'][0]['phone'],
                'opening_hours': self.get_hours(store)
            }

            yield GeojsonPointItem(**properties)

    def get_hours(self, store_data):
        """ Trys to return the hours for a store, some do not list all hours.
            store_data is a dict of the store data, pulled in via scraping. """
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        time_string = ''

        for counter, day in enumerate(days):
            try:
                close_time = store_data['details']['departments'][0]['storeDeptHours'][counter]['closeTime']
            except KeyError as e:        # Ignore key errors as some stores do not list closing hours
                close_time = ''

            try:
                open_time = store_data['details']['departments'][0]['storeDeptHours'][counter]['openTime']

            except KeyError as e:
                open_time = ''

            time_string = ''.join([time_string, day, ' ', open_time, ' - ', close_time, ';'])

        return time_string 
