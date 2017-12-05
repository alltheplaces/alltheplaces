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
        form_data = {
            'address': '90210',
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

