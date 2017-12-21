import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS_NAME = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

class QdobaSpider(scrapy.Spider):
    name = "qdoba"
    allowed_domains = ["prod.qdoba.bottlerocketservices.com"]
    start_urls = (
        'https://prod.qdoba.bottlerocketservices.com/api/v1/query/store/locate/lat/40.7127753/lon/-74.0059728/radius/30',
    )

    def store_hours(self, stores_data):
        if len(stores_data) == 0:
            return None

        day_groups = []
        this_day_group = None
        store_hours = [None] * len(stores_data)

        for item in stores_data:
            store_hours[item['dayOfWeek'] - 1] = item


        for day_info in store_hours:

            day = DAYS_NAME[day_info['dayOfWeek'] - 1]
            hours = day_info['timeWindows']

            match_o = re.match('(\d{1,2})\:(\d{2})', hours[0]['openingTime'])
            match_c = re.match('(\d{1,2})\:(\d{2})', hours[0]['closingTime'])
            h_o, m_o = match_o.groups()
            h_c, m_c = match_c.groups()

            hours = '%02d:%02d-%02d:%02d' % (
                int(h_o),
                int(m_o),
                int(h_c),
                int(m_c),
            )

            if not this_day_group:
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        opening_hours = ""

        for day_group in day_groups:
            if day_group['from_day'] == day_group['to_day']:
                opening_hours += '{from_day} {hours}; '.format(**day_group)
            elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                opening_hours += '{hours}; '.format(**day_group)
            else:
                opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
        opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        try:
            stores = json.loads(response.body_as_unicode())
            stores = stores.get('results')
        except:
            raise

        for store in stores:
            props = {}
            try:
                phone = store.get('contactInfo')['cateringPhone']
            except:
                phone = ''

            props['ref'] = store.get('id')
            props['city'] = store.get('address')['city']
            props['state'] = store.get('address')['state']
            props['lat'] = store.get('geoLoc')['lat']
            props['lon'] = store.get('geoLoc')['lon']
            props['street'] = store.get('address')['street']
            props['name'] = store.get('name')
            props['phone'] = phone
            props['postcode'] = store.get('address')['postal']
            props['opening_hours'] = self.store_hours(store.get('hoursOfOperation'))

            yield GeojsonPointItem(**props)
