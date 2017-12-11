import json
import requests
import scrapy
from urllib import parse
from locations.items import GeojsonPointItem


MAPQUEST_KEY = 'ybe4KeKi8ACKY0eVqJXAw2QxTKnxnor8'

MAPQ = 'http://www.mapquestapi.com/geocoding/v1/address?'

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


class WawaSpider(scrapy.Spider):
    name = 'wawa'
    start_urls = (
        'https://www.wawa.com/Handlers/LocationByLatLong.ashx?',
    )
    download_delay = 1.5
    allowed_domains = ('www.wawa.com', 'www.mapquestapi.com', )

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
                'lat': lat,
                'lon': lng,
                'opening_hours': opening_hours
            }
            return GeojsonPointItem(**properties)

    def start_requests(self):

        url = self.start_urls[0]
        for state in STATES:
            params = [('key', MAPQUEST_KEY), ('location', state)]
            url = MAPQ + parse.urlencode(params)
            data = requests.get(url).json()

            if data.get('results', {}):
                lat, lng = data['results'][0]['locations'][0]['latLng'].values()

                wawa_params = {'limit': 50, 'lat': lat, 'long': lng}
                wawa_url = self.start_urls[0] + parse.urlencode(wawa_params)

                yield scrapy.Request(
                    wawa_url,
                    headers={
                        'Accept': 'application/json',
                    },
                    callback=self.parse
                )
