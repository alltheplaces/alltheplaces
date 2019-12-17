import json
import re
import scrapy
from locations.items import GeojsonPointItem
DAYS = {
    'mo': 'Mo',
    'tu': 'Tu',
    'we': 'We',
    'fr': 'Fr',
    'th': 'Th',
    'sa': 'Sa',
    'su': 'Su',
}
class TescoSpider(scrapy.Spider):
    name = "tesco"
    item_attributes = { 'brand': "Tesco" }
    allowed_domains = ["tescolocation.api.tesco.com"]
    def store_hours(self, store_hours):
        clean_time=''
        for key, value in store_hours.items():
           if('isOpen' in value and 'open' in value and 'close' in value):
            if(value['isOpen']=='true'):
              clean_time = clean_time + DAYS[key]+' '+value['open'][0:2]+':'+value['open'][2:]+'-'+value['close'][0:2]+':'+value['close'][2:]+';'
            else:
              clean_time = clean_time + DAYS[key]+' '+'Closed'+';'

        return clean_time
    def start_requests(self):
        url = 'https://tescolocation.api.tesco.com/v3/locations/search?offset=0&limit=1000000&sort=near:%2251.499207299999995,-0.08800609999999999%22&filter=category:Store%20AND%20isoCountryCode:x-uk&fields=name,geo,openingHours,altIds.branchNumber,contact'

        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.tesco.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.kfc.com/store-locator?query=90210',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'x-appkey':'store-locator-web-cde'
        }


        yield scrapy.http.FormRequest(
                url=url, method='GET',
                headers=headers, callback=self.parse
            )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['results']


        for store in stores:
            addr_full=''
            for add in store['location']['contact']['address']['lines']:
                addr_full=addr_full+' '+add['text']
            properties = {
                'ref': store['location']['id'],
                'name': store['location']['name'],
                'addr_full': addr_full,
                'city': store['location']['contact']['address']['town'],
                'state': '',
                'country':'United Kingdom',
                'postcode': store['location']['contact']['address']['postcode'],
                'lat': store['location']['geo']['coordinates']['latitude'],
                'lon':  store['location']['geo']['coordinates']['longitude'],
                'phone': store['location']['contact']['phoneNumbers'][0]['number'],
            }

            opening_hours = self.store_hours(store['location']['openingHours'][0]['standardOpeningHours'])
            if opening_hours:
                properties['opening_hours'] = opening_hours

            yield GeojsonPointItem(**properties)


