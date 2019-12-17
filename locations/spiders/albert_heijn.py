# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

class AlbertHeijnSpider(scrapy.Spider):
    name = 'albert_heijn'
    item_attributes = { 'brand': "Albert Heijn" }
    allowed_domains = ['www.ah.nl']

    def start_requests(self):
        url = 'https://www.ah.nl/data/winkelinformatie/winkels/json'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        for store in stores['stores']:
            yield GeojsonPointItem(
                lat = store['lat'],
                lon = store['lng'],
                addr_full = store['street'],
                city = store['city'],
                phone = store['phoneNumber'],
                state = "",
                postcode = store['zip'],
                ref = store['no'],
                country = "Netherlands",
                website = "https://www.ah.nl/winkel/albert-heijn/%s/%s/%s"%(store['city'],store['street'],store['no'])
                )