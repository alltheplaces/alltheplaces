import json
import re
import scrapy
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

URL = 'https://mktsvc.tjx.com/storelocator/GetSearchResultsByState'


NORMALIZE_KEYS = (
    ('addr_full', ['Address', 'Address2']),
    ('city', ['City']),
    ('state', ['State']),
    ('postcode', ['Zip']),
    ('country', ['Country']),
    ('phone', ['Phone']),
)


def normalize_time(hours):

    if not hours:
        return ''

    day_times = hours.split(',')
    normalize_day_times = []

    for day_time in day_times:
        day, hours = [x.strip() for x in day_time.split(': ')]
        normalize_hours = []

        if re.search('-', day):
            days = [x.strip() for x in day.split('-')]
            norm_days = '-'.join([DAYS.get(x, '') for x in days])
        else:
            norm_days = DAYS.get(day, '')

        if re.search('CLOSED', hours):
            norm_hours = ' off'
            normalize_hours.append(norm_hours)
        else:
            if re.search('-', hours):
                hours = [x.strip() for x in hours.split('-')]

                for hour in hours:

                    if hour[-1] == 'p':
                        if re.search(':', hour[:-1]):
                            hora, minute = [x.strip() for x in hour[:-1].split(':')]
                            if int(hora) < 12:
                                norm_hours = str(int(hora) + 12) + ':' + minute
                        else:
                            if int(hour[:-1]) < 12:
                                norm_hours = str(int(hour[:-1]) + 12) + ":00"

                    elif hour[-1] == 'a':
                        if re.search(':', hour[:-1]):
                            hora, minute = [x.strip() for x in hour[:-1].split(':')]
                            norm_hours = hora + ':' + minute
                        else:
                            norm_hours = hour[:-1] + ":00"

                    normalize_hours.append(norm_hours)

        normalize_day_times.append(' '.join([norm_days, '-'.join(normalize_hours)]))
    return '; '.join(normalize_day_times)


class MarshallsSpider(scrapy.Spider):

    name = "marshalls"
    item_attributes = { 'brand': "Marshalls" }
    allowed_domains = ["mktsvc.tjx.com", 'www.marshallsonline.com']

    def start_requests(self):
        url = URL

        headers = {
            'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
            'Origin': 'https://www.marshallsonline.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.marshallsonline.com/store-finder/by-state',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        for state in STATES:
            form_data = {'chain': '10', 'lang': 'en', 'state': state}

            yield scrapy.http.FormRequest(url=url, method='POST', formdata=form_data,
                                          headers=headers, callback=self.parse)

    def parse(self, response):

        data = json.loads(response.body_as_unicode())
        stores = data.get('Stores', None)
        props = {}

        for store in stores:
            props['lat'] = store.pop('Latitude', None)
            props['lon'] = store.pop('Longitude', None)
            props['ref'] = store.pop('StoreID', None)
            props['website'] = URL

            for new_key, old_keys in NORMALIZE_KEYS:
                props[new_key] = ", ".join([store.pop(key, '').strip() for key in old_keys if store[key]])

            opening_hours = normalize_time(store.pop('Hours', ''))

            if opening_hours:
                props['opening_hours'] = opening_hours
                props.pop('Hours', None)

            yield GeojsonPointItem(**props)
