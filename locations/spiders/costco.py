# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

HEADERS = {
           'Host': 'www.costco.com',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'en-US,en;q=0.9',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Connection': 'keep-alive',
           'Cache-Control': 'max-age=0',
           'Upgrade-Insecure-Requests': '1',
           'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           }
URL = 'https://www.costco.com/AjaxWarehouseBrowseLookupView?langId=-1&storeId=10301&numOfWarehouses=10&hasGas=false&hasTires=false&hasFood=false&hasHearing=false&hasPharmacy=false&hasOptical=false&hasBusiness=false&tiresCheckout=0&isTransferWarehouse=false&populateWarehouseDetails=true&warehousePickupCheckout=false&latitude=42.0031051635742&longitude=-89.9876327514648'

class CostcoSpider(scrapy.Spider):
    name = "costco"
    allowed_domains = ['www.costco.com']

    def start_requests(self):
        form_data = {'action': 'udfd_update_locations', 'data': '3211'}

        yield scrapy.http.FormRequest(url=URL, method='GET', headers=HEADERS, callback=self.parse)

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
        days_name = {'m':'Mo', 't':'Tu', 'w':'We', 's':'Si', 'f':'Fr'}

        for day_info in store_hours:
            if day_info.lower().find('close') > -1:
                continue

            match = re.match('(.*)\s(.*)\s-\s(.*)$', day_info)
            day, day_open, day_close = match.groups()
            day = day.split('-')

            if len(day) == 2:
                day = days_name[day[0].lower()] + '-' + days_name[day[1].lower()]
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
        stores = json.loads(response.body_as_unicode())

        for store in stores:

            props = {
                'lat': store.get('latitude'),
                'lon': store.get('longitude'),
                'ref': str(store.get('identifier')),
                'phone': self._clean_text(store.get('phone')),
                'name': store.get('displayName'),
                'addr_full': store.get('address1'),
                'city': store.get('city'),
                'state': store.get('state'),
                'postcode': store.get('zipCode'),
                'website': store.get('url'),
                'opening_hours': self.store_hours(store.get('warehouseHours')),
            }

            yield GeojsonPointItem(**props)

    def _clean_text(sel, text):
        return re.sub("[\r\n\t]", "", text).strip()