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
    'sun. ': 'Su',
    'sat': 'Sa',
}


class CostcoSpider(scrapy.Spider):
    name = "costco"
    allowed_domains = ['www.costco.com']
    start_urls = (
        'https://www.costco.com/WarehouseLocatorBrowseView',
    )
    download_delay = 0.3
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0',
    }

    def normalize_time(self, time_str):
        match = re.search(r'(.*)(am|pm| a.m| p.m)', time_str)
        h, am_pm = match.groups()
        h = h.split(':')

        return '%02d:%02d' % (
            int(h[0]) + 12 if am_pm == u' p.m' or am_pm == u'pm' else int(h[0]),
            int(h[1]) if len(h) > 1 else 0,
        )

    def store_hours(self, store_hours):
        opening_hours = []

        if not store_hours:
            return None

        for day_info in store_hours:
            if day_info.lower().find('close') > -1:
                continue

            match = re.match('(.*)\s(.*)\s-\s(.*)$', day_info)
            day, day_open, day_close = match.groups()
            day = day.split('-')

            if len(day) == 2:
                day = DAYS_NAME[day[0].lower()] + '-' + DAYS_NAME[day[1].lower()]
            else:
                day = day[0][:2]

            day_hours = '{} {}:{}'.format(
              day,
              self.normalize_time(day_open),
              self.normalize_time(day_close),
            )

            opening_hours.append(day_hours)

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
