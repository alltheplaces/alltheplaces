import json
import re
import scrapy
from urllib import parse

from locations.items import GeojsonPointItem
from locations.states_counties import state_county

NORMALIZE_KEYS = (
    ('addr_full', 'cafeStreetName'),
    ('city', 'cafeCity'),
    ('state', 'cafeState'),
    ('postcode', 'cafeZip'),
    ('phone', 'cafeContact'),
)
URL = 'https://www.panerabread.com/pbdyn/panerabread/searchcafe?'


class PanerabreadSpider(scrapy.Spider):

    name = "panerabread"
    allowed_domains = ["panerabread.com"]
    download_delay = 1.5

    def start_requests(self):

        headers = {
            'Accept-Language': '*/*',
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

                yield scrapy.http.Request(
                    url=full_url,
                    headers=headers,
                    callback=self.parse
                )

    def store_hours(self, hours):
        matches = re.findall(r"(\S{3}):{'open':'(\S{5})','close':'(\S{5})'}", hours)

        this_day_group = {}
        day_groups = []
        for day, open_time, close_time in matches:
            day_short = day[:2]
            hours_today = '{}-{}'.format(open_time, close_time)

            if not this_day_group:
                this_day_group = {
                    'from_day': day_short,
                    'to_day': day_short,
                    'hours': hours_today,
                }
            elif hours_today == this_day_group['hours']:
                this_day_group['to_day'] = day_short
            elif hours_today != this_day_group['hours']:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day_short,
                    'to_day': day_short,
                    'hours': hours_today,
                }
        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            opening_hours = day_groups[0]['hours']
            if opening_hours == '07:00-07:00':
                opening_hours = '24/7'
        else:
            opening_hours = ''
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data.get('features', [])

        for store in stores:
            props = {
                'lat': float(store['lat']),
                'lon': float(store['lng']),
                'ref': store['cafeID'],
                'website': response.url,
            }

            for new_key, old_key in NORMALIZE_KEYS:
                props[new_key] = str(store.get(old_key))

            opening_hours = self.store_hours(store.get('cafeHours', ''))
            if opening_hours:
                props['opening_hours'] = opening_hours

            yield GeojsonPointItem(**props)
