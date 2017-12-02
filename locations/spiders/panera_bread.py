import json
import re
import scrapy
from urllib import parse

from locations.items import GeojsonPointItem


STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


DAYS = {'Mon': 'Mo', 'Tue': 'Tu',
        'Wed': 'We', 'Thu': 'Th',
        'Fri': 'Fr', 'Sat': 'Sa',
        'Sun': 'Su'}


NORMALIZE_KEYS = (
    ('addr:full', 'cafeStreetName'),
    ('addr:city', 'cafeCity'),
    ('addr:state', 'cafeState'),
    ('addr:postcode', 'cafeZip'),
    ('phone', 'cafeContact'),
)

URL = 'https://www.panerabread.com/pbdyn/panerabread/searchcafe?'



class PanerabreadSpider(scrapy.Spider):

    name = "panerabread"
    allowed_domains = ["panerabread.com"]

    def start_requests(self):

        headers = {'Accept-Language': '*/*',
                   'Origin': 'https://www.panerabread.com',
                   'Accept-Encoding': 'gzip, deflate, sdch, br',
                   'Accept': 'application/json, text/plain, */*',
                   'Connection': 'keep-alive',
                   'Content-Type': 'text/javascript; charset=UTF-8',
                   }

        for state in STATES:
            full_url = URL
            new_url = [('address', state), ('limit', '10')]
            encoded_url = parse.urlencode(new_url)
            full_url += encoded_url

            yield scrapy.http.Request(url=full_url, headers=headers,
                                      callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data.get('features', [])
        opening_hours = ''
        props = {}

        for store in stores:
            lon_lat = [float(store.pop('lng', None)),
                       float(store.pop('lat', None))]
            props['ref'] = store.pop('cafeID', '')
            props['website'] = URL

            for new_key, old_key in NORMALIZE_KEYS:
                props[new_key] = str(store.pop(old_key, ''))

            yield GeojsonPointItem(
                properties=props,
                lon_lat=lon_lat
            )
