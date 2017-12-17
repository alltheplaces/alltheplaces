# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS_NAME = {
    'm': 'Mo',
    't': 'Tu',
    'w': 'We',
    's': 'Th',
    'f': 'Fr',
    'f ': 'Fr',
    'sun': 'Su',
    'sat': 'Sa',
    'daily': '',
}


class CostcoSpider(scrapy.Spider):
    name = "costco"
    allowed_domains = ['www.costco.com']
    start_urls = (
        'https://www.costco.com/WarehouseLocatorBrowseView',
    )
    download_delay = 0.5
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0',
    }

    def store_hours(self, store_hours):
        opening_hours = []

        if not store_hours:
            return None

        for day_info in store_hours:
            if day_info.lower().find('close') > -1:
                continue

            match = re.match(r'^(\w+)-?\.?([A-Za-z]*)\.? *(\d{1,2}):(\d{2}) ?(am|pm|) *- +(\d{1,2}):(\d{2}) ?(am|pm|hrs\.)$', day_info)
            if not match:
                self.logger.warn("Couldn't match hours: %s", day_info)

            try:
                day_from, day_to, fr_hr, fr_min, fr_ampm, to_hr, to_min, to_ampm = match.groups()
            except ValueError:
                self.logger.warn("Couldn't match hours: %s", day_info)
                raise

            day_from = DAYS_NAME[day_from.lower()]
            day_to = DAYS_NAME[day_to.lower()] if day_to else day_from

            if day_from != day_to:
                day_str = '{}-{}'.format(day_from, day_to)
            else:
                day_str = '{}'.format(day_from)

            day_hours = '%s %02d:%02d-%02d:%02d' % (
                day_str,
                int(fr_hr) + 12 if fr_ampm == 'pm' else int(fr_hr),
                int(fr_min),
                int(to_hr) + 12 if to_ampm == 'pm' else int(to_hr),
                int(to_min),
            )

            opening_hours.append(day_hours.strip())

        return '; '.join(opening_hours)

    def parse(self, response):
        container_ids = response.xpath('//div[@class="form-item statePanel"]/select/option/@value').extract()
        for container_id in container_ids:
            yield scrapy.Request(
                'https://www.costco.com/AjaxWarehouseBrowseLookupView?catalogId=10701&parentGeoNode=' + container_id,
                callback=self.parse_stores
            )

    def parse_stores(self, response):
        stores = json.loads(response.body_as_unicode())

        for store in stores:
            props = {
                'lat': store.get('latitude'),
                'lon': store.get('longitude'),
                'ref': store.get('identifier'),
                'phone': self._clean_text(store.get('phone')),
                'name': store.get('displayName'),
                'addr_full': store.get('address1'),
                'city': store.get('city'),
                'state': store.get('state'),
                'postcode': store.get('zipCode'),
                'country': store.get('country'),
                'website': 'https://www.costco.com/warehouse-locations/store-{}.html'.format(store.get('identifier')),
                'opening_hours': self.store_hours(store.get('warehouseHours')),
            }

            yield GeojsonPointItem(**props)

    def _clean_text(sel, text):
        return re.sub("[\r\n\t]", "", text).strip()
