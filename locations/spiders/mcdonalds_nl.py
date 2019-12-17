import json
import re
import scrapy
from locations.items import GeojsonPointItem

class McDonaldsNLSpider(scrapy.Spider):
    name = "mcdonalds_nl"
    brand = "McDonald's"
    allowed_domains = ["mcdonalds.nl"]

    def start_requests(self):
        url = 'https://mcdonalds.nl/restaurant'
        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://mcdonalds.nl',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Referer': 'https://mcdonalds.nl/restaurant',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
        }
        form_data = {
            'lat':'53.0185209',
            'lon':'6.559760099999949',
            'distance':'500',
            'action':'getLocations',
            'storelocator_v2':'true'
        }

        yield scrapy.http.FormRequest(
            url=url, method='POST', formdata=form_data,
            headers=headers, callback=self.parse
        )

    def store_hours(self, data):
        day = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        day_groups = []
        this_day_group = {}
        day_hours = data["openTimes"]
        for day_hour in day_hours:
            hours = ''
            weekday, start, end = day_hour["weekday"], day_hour["open"], day_hour["close"]

            short_day = day[weekday]
            hours = '{}:{}-{}:{}'.format(start[:2], start[3:], end[:2], end[3:])
            if not this_day_group:
                this_day_group = {
                    'from_day': short_day,
                    'to_day': short_day,
                    'hours': hours,
                }

            elif hours == this_day_group['hours']:
                this_day_group['to_day'] = short_day

            elif hours != this_day_group['hours']:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': short_day,
                    'to_day': short_day,
                    'hours': hours,
                }

        day_groups.append(this_day_group)

        if not day_groups:
            return None
        opening_hours = ''
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours [:-2]

        return opening_hours

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        index = 0
        for store in stores:
            properties = {
                'ref': index,
                'name': store['title'],
                'addr_full': store['address'],
                'city': store['city'],
                'website': store['website'],
                'postcode': store['postal_code'],
                'lat': store['lat'],
                'lon': store['lon'],
            }

            opening_hours = self.store_hours(store)
            if opening_hours:
                properties['opening_hours'] = opening_hours

            index = index + 1

            yield GeojsonPointItem(**properties)

