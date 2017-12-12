# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.7-eleven.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'application/json',
    'Referer': 'https://www.7-eleven.com/locator',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-SEI-TZ': '-08:00',
    'Authorization': 'Bearer r7EzhnRW1tUCDIR8jUPmyqTpPK7m54'
}


class SevenElevenSpider(scrapy.Spider):
    name = "seven_eleven"
    allowed_domains = ["www.7-eleven.com"]
    start_urls = (
        'https://api.7-eleven.com/v4/stores/?lat=40.72786721004897&lon=-73.96717732880859&features=&radius=88.5137&limit=500&curr_lat=40.72786721004897&curr_lon=-73.96717732880859',
    )

    
    def start_requests(self):

        url = self.start_urls[0]

        yield scrapy.Request(url=url, headers=HEADERS, callback=self.parse)


    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data['results']:
            properties = {
                "ref": store['id'],
                "name": store['name'],
                "opening_hours": store['hours']['operating'],
                "addr_full": store['address'],
                "city": store['city'],
                "state": store['state'],
                "postcode": store['zip'],
                "country": store['country'],
                "lon": float(store['lon']),
                "lat": float(store['lat']),
                "phone": store['phone'],
            }

            yield GeojsonPointItem(**properties)

        next_url = data['next']
        if next_url is not None:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(url=next_url, headers=HEADERS, callback=self.parse)

