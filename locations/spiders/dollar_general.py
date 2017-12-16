# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

class DollarGeneralSpider(scrapy.Spider):
    name = 'dollar_general'
    allowed_domains = ['hosted.where2getit.com']
        
    def start_requests(self):
        url = 'https://hosted.where2getit.com/dollargeneral/rest/locatorsearch?lang=fr_FR'
        for state in STATES:
            formdata = {  
                'request':{  
                    'appkey':'9E9DE426-8151-11E4-AEAC-765055A65BB0',
                    'formdata':{  
                        'geoip':'false',
                        'dataview':'store_default',
                        'geolocs':{  
                            'geoloc':[  
                                {  
                                    'addressline':state,
                                    'country':'US'
                                }
                            ]
                        },
                        'searchradius':'100'
                    }
                }
            }

            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/json',
                'Origin': 'https://hosted.where2getit.com',
                'Host':'hosted.where2getit.com',
                'Referer': 'https://hosted.where2getit.com/dollargeneral/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            yield scrapy.http.Request(
                url, 
                self.parse,
                method = 'POST',
                body = json.dumps(formdata),
                headers = headers,
            )

    def parse(self, response):
        result = json.loads(response.body_as_unicode())

        if 'collection' in result['response'].keys():
            for data in result['response']['collection'] :
                ref = data['uid']
                lat = data['latitude']
                lon = data['longitude']
                name = data['name']
                state = data['state']
                street = data['address1']
                city = data['city']
                phone = data['phone']
                opening_hours = self.hours(data)
                postalcode = 'postalcode' in data.keys() and re.search(r'\d+', data['postalcode']).group() or ''

                properties = {
                    "phone"         : phone,
                    "ref"           : ref,
                    "name"          : name,
                    "opening_hours" : opening_hours,
                    "lat"           : lat,
                    "lon"           : lon,
                    "street"        : street,
                    "city"          : city,
                    "state"         : state,
                    "postcode"      : postalcode
                }
                
                yield GeojsonPointItem(**properties)

    def hours(self, data):
        hours = ''
        for weekday in WEEKDAYS :
            if 'opening_time_' + weekday.lower() in data.keys():
                hours = hours + '{} {}-{}; '.format(weekday[:2], data['opening_time_' + weekday.lower()], data['closing_time_' + weekday.lower()])

        return hours