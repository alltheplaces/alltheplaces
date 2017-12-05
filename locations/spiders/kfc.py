import json
import re
import scrapy
from locations.items import GeojsonPointItem


class KFCSpider(scrapy.Spider):
    name = "kfc"
    allowed_domains = ["www.kfc.com"]

    def normalize_time(self, time_str):
        match = re.search(r'(\d{1,2}):(\d{2})([AP])M', time_str)
        h, m, am_pm = match.groups()

        return '%02d:%02d' % (
            int(h) + 12 if am_pm == 'P' else int(h),
            int(m),
        )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            day_open = store_hours[day + 'Start']
            day_close = store_hours[day + 'End']

            if day_open is False:
                # On days that they're closed they set the value to 'false'
                continue

            day_open = self.normalize_time(day_open)
            day_close = self.normalize_time(day_close)

            hours = day_open + "-" + day_close

            day_short = day.title()[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day_short
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
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

    def start_requests(self):
        url = 'https://services.kfc.com/services/query/locations'

        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.kfc.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.kfc.com/store-locator?query=90210',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }

        zipcodes = ['83253', '57638', '54848', '44333', '03244', '23435', '31023', '38915', '79525', '81321', '89135', '98250', '69154', '62838']

        for zipcode in zipcodes:
            form_data = {
                'address': zipcode,
                'distance': '1000'
            }

            yield scrapy.http.FormRequest(
                url=url, method='POST', formdata=form_data,
                headers=headers, callback=self.parse
            )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['results']
        for store in stores:
            properties = {
                'ref': store['entityID'],
                'name': store['storeNumber'],
                'addr_full': store['addressLine'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['postalCode'],
                'lat': store['latitude'],
                'lon': store['longitude'],
                'phone': store['businessPhone'],
            }

            opening_hours = self.store_hours(store)
            if opening_hours:
                properties['opening_hours'] = opening_hours

            yield GeojsonPointItem(**properties)

