# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']


class HarristeeterSpider(scrapy.Spider):
    name = "harristeeter"
    allowed_domains = ["harristeeter.com"]
    start_urls = (
        'https://www.harristeeter.com/store/#/app/store-locator',
    )

    def store_hours(self, store_hours):
        res=''
        for day in store_hours:
            match = re.search(r'(\w*)(\s*-\s*(\w*))?\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)?\s*-\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)',day.replace('Midnight','12:00pm'))

            if not match:
                continue
            res += match[1][:2]

            try:
                res += match[2].replace(' ','')[:3]+' '
            except Exception:
                res += ' '

            if match[5]:
                first_minutes = match[5]
            else:
                first_minutes = ':00'

            if match[9]:
                second_minutes = match[9]
            else:
                second_minutes = ':00'

            res += str(int(match[4])+(12 if match[7] in ['pm','mp'] else 0)) +first_minutes+'-'
            res += str(int(match[8])+(12 if match[10] in ['pm','mp'] else 0)) +second_minutes+';'

        return res.rstrip(';').strip()

    def parse(self, response):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.harristeeter.com/store/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
        }
        cookies = {
            '_gag': 'MWtPTFViOHlIb3NGbHpvOEV0cEpGN0EvcExBanR1eS9vNVpkbUN1N2xES0xsRWg4NUkyb2JRTC9BSTJOU0QwRXBFdHZRbzZFVXBxdk5ZWURMSGtwR1laa0JURG0wbm1hNzdaYjE1YWtmL3FJWjlnZWxBTHpGTGJBQW1HWkhXdDhNd2lmNnh5ZjRuMWRjMXRQRWdRN3pxWFdJaDhIQjBiZE1JTXY4cjB0T2hqUk5NZGtUT3ZCb3M5YldHa1pnSm9xbk0vRGdzSktQYlBIbXJLMEN3Z0dLaDVpNG9TYlQyQT0%3D',
            '_i': 'bVEvZlFhSkplTWhsNnlSNmI1WUxkL2RUMjg1WXM1ai95dVUwOVVxZy9nQ1VqeDRvZzh2NkwwVzRTbzJYVnpnVnZ5a3hIZHZZSE5xN1R3PT0%3D',
            '_j': 'aXg2SkUvQlVZOU4vK2p4bGNKNEFQNmNCd05kSHJZSGwwdmNzN2xHZy9nQ1VqeDRvZzh2NkwwVzRTbzJYVnpnVnZ5a3hIZHZZSE5xN1R3PT0%3D',
            '_k': 'bVEvZlFhSkplTWhsNnlSNmI1WUxkK1ZDalp3S3JvUGswUFFzNmxXbzlVakUzUVV4bk5Yak5WMnFVcGFNVnpnVnZ5a3hIZHZZSE5xN1R3PT0%3D',
            '_ga': 'GA1.2.1107952112.1513511447',
            '_gid': 'GA1.2.1016975193.1513511447',
            '_gat': '1',
            'HTAPIADMSESID': 's%3Alh3qzQLiIT5mVgmOvYNMN2EqZJZYU8NU.pkHP40HGnq1sZQuq%2FqeOUv3Xh1B%2BbvWE739hwwdTp0g',
        }

        yield scrapy.Request(
            'https://www.harristeeter.com/api/v1/stores/search?Address=98011&Radius=20000&AllStores=true',
            headers=headers,
            cookies=cookies,
            callback=self.parse_shop
        )

    def parse_shop(self, response):
        shops = json.loads(response.text)['Data']

        for shop in shops:
            props = {
                'opening_hours': shop['StoreHours'].replace('Open 24 hrs', 'Mo-Su 0:00-24:00'),
                'phone': shop['Telephone'],
                'country': shop['Country'],
                'ref': shop['Title'],
                'addr_full': shop['Street'],
                'postcode': shop.get('ZipCode'),
                'city': shop.get('City'),
                'state': shop.get('State'),
                'lat': float(shop['Latitude']),
                'lon': float(shop['Longitude']),
            }

            yield GeojsonPointItem(**props)
