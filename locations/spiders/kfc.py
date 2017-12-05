import json
import re
import scrapy
from locations.items import GeojsonPointItem


class KFCSpider(scrapy.Spider):
    name = "kfc"
    allowed_domains = ["www.kfc.com"]

    def start_requests(self):
        url = 'https://services.kfc.com/services/query/locations'

        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.kfc.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.kfc.com/store-locator?query=90210',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }

        zipcodes = ['90001', '10022', '33614', '90210', '10001', '10013', '10012', '10021', '10024', '10023', '10014', '22314',
                '20001', '33132', '33143', '33125', '33142', '10025', '10005', '10002', '10003', '10004', '10011', '10010',
                '90014', '90010', '90069', '90022', '23451', '63101', '30303', '20005', '20036', '82941', '30324', '30022',
                '30004', '30005', '98052', '21201', '99362', '07054', '22313', '98065', '90089', '90213', '90209', '32801',
                '32837', '77002', '10451']

        for zipcode in zipcodes:
            form_data = {
                'address': zipcode,
                'distance': '100'
            }

            yield scrapy.http.FormRequest(
                url=url, method='POST', formdata=form_data,
                headers=headers, callback=self.parse
            )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['results']
        for store in stores:
            properties = {
                'ref': store['entityID'],
                'name': store['storeNumber'],
                'addr_full': store['addressLine'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['postalCode'],
                'lat': store['latitude'],
                'lon': store['longitude'],
                'phone': store['businessPhone'],
                'opening_hours': 'Mo-Su 09:30-23:00'
            }

            yield GeojsonPointItem(**properties)

