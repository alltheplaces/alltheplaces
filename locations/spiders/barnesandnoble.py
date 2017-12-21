# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class BarnesandnobleSpider(scrapy.Spider):
    name = "barnesandnoble"
    allowed_domains = ["stores.barnesandnoble.com"]
    start_urls = (
        'https://stores.barnesandnoble.com/stores?searchText=60001&view=map&storeFilter=all',
    )

    def store_hours(self, store_hours):
        opening_hours = []
        store_hours = store_hours.split(', ')

        for day_info in store_hours:
            if day_info.lower().find('close') > -1:
                continue

            match = re.match('(\w+)?\-?\&?(.*?)\s(\d{1,2})-(\d{1,2})', day_info)
            if not match:
                self.logger.warn("Couldn't match hours: %s", day_info)

            try:
                day_from, day_to, fr_hr, to_hr = match.groups()
            except ValueError:
                self.logger.warn("Couldn't match hours: %s", day_info)
                raise

            day_from = day_from[:2]
            day_to = day_to[:2] if day_to[:2] != '' else day_from

            if day_from != day_to:
                day_str = '{}-{}'.format(day_from, day_to)
            else:
                day_str = '{}'.format(day_from)

            day_hours = '%s %02d:%02d-%02d:%02d' % (
                day_str,
                int(fr_hr),
                0,
                int(to_hr) + 12,
                0,
            )

            opening_hours.append(day_hours.strip())

        return '; '.join(opening_hours)

    def parse(self, response):
        content = response.body_as_unicode()
        stores = json.loads(re.search('var storesJson = (.*)\;', content).group(1))

        for store in stores:
            props = {}
            props['ref'] = store.get('storeId')
            props['city'] = store.get('city')
            props['state'] = store.get('state')
            props['lat'] = store.get('location')[1]
            props['lon'] = store.get('location')[0]
            props['addr_full'] = store.get('address1')
            props['street'] = store.get('address2')
            props['name'] = store.get('name')
            props['phone'] = store.get('phone')
            props['postcode'] = store.get('zip')
            props['opening_hours'] = self.store_hours(store.get('hours'))

            yield GeojsonPointItem(**props)
