import json
import re
import scrapy
from urllib import parse

from locations.items import GeojsonPointItem
from locations.states_counties import state_county


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


def updated_time(hours):

    hours = re.sub("[}{\]\[\']", "", hours)
    hours = re.sub(':open:', ' ', hours)
    hours = re.sub(',close:', '-', hours)
    days_hours = hours.split(',')
    days = [re.sub(x[:3], DAYS[x[:3]], x) for x in days_hours]

    return ";".join(days)


class PanerabreadSpider(scrapy.Spider):

    name = "panerabread"
    allowed_domains = ["panerabread.com"]
    download_delay = 1.5

    def start_requests(self):

        headers = {'Accept-Language': '*/*',
                   'Origin': 'https://www.panerabread.com',
                   'Accept-Encoding': 'gzip, deflate, sdch, br',
                   'Accept': 'application/json, text/plain, */*',
                   'Connection': 'keep-alive',
                   'Content-Type': 'text/javascript; charset=UTF-8',
                   }

        for state, counties in state_county.items():
            for county in counties:
                full_url = URL
                new_url = [('address', county + ", " + state), ('limit', '10')]
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
            props['website'] = response.url

            for new_key, old_key in NORMALIZE_KEYS:
                props[new_key] = str(store.pop(old_key, ''))

            opening_hours = updated_time(store.pop('cafeHours', ''))
            if opening_hours:
                props['opening_hours'] = opening_hours

            yield GeojsonPointItem(
                properties=props,
                lon_lat=lon_lat
            )
