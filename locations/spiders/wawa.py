import json
import scrapy
from six.moves.urllib.parse import urlencode
from locations.items import GeojsonPointItem


MAPQUEST_KEY = 'ybe4KeKi8ACKY0eVqJXAw2QxTKnxnor8'

MAPQ = 'http://www.mapquestapi.com/geocoding/v1/address?'

LAT_LONS = [
    ('39.2601', '-76.3549'),
    ('36.9874', '-77.0031'),
    ('27.9998', '-81.6064'),
    ('38.9300', '-77.1020'),
    ('39.0495', '-75.4541'),
    ('41.2033', '-77.1945'),
    ('40.7995', '-77.8271'),
]


class WawaSpider(scrapy.Spider):
    name = 'wawa'
    start_urls = (
        'https://www.wawa.com/Handlers/LocationByLatLong.ashx?',
    )
    download_delay = 1.5
    allowed_domains = ('www.wawa.com', 'www.mapquestapi.com', )

    def start_requests(self):
        url = 'https://www.wawa.com/Handlers/LocationByLatLong.ashx?'
        for lat, lon in LAT_LONS:
            wawa_params = {'limit': 50, 'lat': lat, 'long': lon}

            yield scrapy.Request(
                url + urlencode(wawa_params),
                headers={
                    'Accept': 'application/json',
                },
                callback=self.parse
            )

    def get_addr(self, addr):
        return (v for k, v in addr.items() if k in ['address', 'city', 'state', 'zip'])

    def get_lat_lng(self, physical_addr):
        return physical_addr['loc']

    def get_opening_hours(self, store):
        open_time = store['storeOpen'][:5]
        close_time = store['storeClose'][:5]

        times = '{}-{}'.format(open_time, close_time)

        if times == '00:00-00:00':
            return '24/7'
        else:
            return times

    def parse(self, response):
        wawa_stores = json.loads(response.body_as_unicode())

        for loc in wawa_stores['locations']:

            addr, city, state, zipc = self.get_addr(loc['addresses'][0])
            lat, lng = self.get_lat_lng(loc['addresses'][1])
            opening_hours = self.get_opening_hours(loc) or None

            properties = {
                'addr_full': addr,
                'name': loc['storeName'],
                'phone': loc['telephone'],
                'city': city,
                'state': state,
                'postcode': zipc,
                'ref': loc['locationID'],
                'website': "https://www.wawa.com/stores/{}/{}".format(
                    loc['locationID'],
                    loc['addressUrl'],
                ),
                'lat': float(lat),
                'lon': float(lng),
                'opening_hours': opening_hours
            }

            yield GeojsonPointItem(**properties)
