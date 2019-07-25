# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

URL = 'https://www.brookdale.com/bin/brookdale/community-search?care_type_category=resident&loc=&finrpt=&state='

US_STATES = (
       "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
       "ID", "IL", "IN", "IA", "KS", "KY", "LA", "MD",
       "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
       "NM", "NY", "NC", "OH", "OK", "OR", "PA", "RI", "SC",
       "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
)

class TemplateSpider(scrapy.Spider):
    name = "brookdale"
    allowed_domains = ["www.brookdale.com"]

    def start_requests(self):
        for state in US_STATES:
            url = ''.join([URL, state])
            yield scrapy.Request(url, callback=self.parse_info)


    def parse_info(self, response):

        data = json.loads(response.body_as_unicode())

        i = 0
        while i < len(data):

            print(data[i]['name'])
            properties = {
                "ref": data[i]['community_id'],
                "name": data[i]['name'],
                "lat": data[i]['latitude'],
                "lon": data[i]['longitude'],
                "addr_full": data[i]['address1'],
                "city": data[i]['city'],
                "state": data[i]['state'],
                "country": data[i]['country_code'],
                "postcode": data[i]['zip_postal_code'],
                "website": data[i]['website'],
                "phone": data[i]['contact_center_phone'],
            }

            yield GeojsonPointItem(**properties)
            i += 1