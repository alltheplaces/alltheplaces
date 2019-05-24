# -*- coding: utf-8 -*-
import scrapy
import json
import re
from urllib.parse import urlencode

from locations.items import GeojsonPointItem

DAYS_NAME = {
    'm': 'Mo',
    'mon': 'Mo',
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

    download_delay = 0.5
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0',
    }

    def start_requests(self):
        url = 'https://www.costco.com/AjaxWarehouseBrowseLookupView?'

        params = {
            "langId": "-1",
            # "storeId": "10301",
            "numOfWarehouses": "50", # max allowed
            "hasGas": "false",
            "hasTires": "false",
            "hasFood": "false",
            "hasHearing": "false",
            "hasPharmacy": "false",
            "hasOptical": "false",
            "hasBusiness": "false",
            "hasPhotoCenter": "false",
            "tiresCheckout": "0",
            "isTransferWarehouse": "false",
            "populateWarehouseDetails": "true",
            "warehousePickupCheckout": "false",
            "countryCode": "US",
        }

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.split(',')
                params.update({"latitude": lat, "longitude": lon})
                yield scrapy.Request(url=url + urlencode(params))


    def store_hours(self, store_hours):
        opening_hours = []

        if not store_hours:
            return None

        for day_info in store_hours:
            if day_info.lower().find('close') > -1:
                continue

            match = re.match(r'^(\w+)-?[\.:]?([A-Za-z]*)\.? *(\d{1,2}):(\d{2}) ?(am|pm|) *- +(\d{1,2}):(\d{2}) ?(am|pm|hrs\.)$', day_info)
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

    def _clean_text(sel, text):
        return re.sub("[\r\n\t]", "", text).strip()

    def parse(self, response):
        body = json.loads(response.body_as_unicode())


        for store in body[1:]:
            if store["distance"] < 110:
                # only process stores that are within 110 miles of query point
                # (to reduce processing a ton of duplicates)
                ref = store['identifier']
                properties = {
                    'lat': store.get('latitude'),
                    'lon': store.get('longitude'),
                    'ref': ref,
                    'phone': self._clean_text(store.get('phone')),
                    'name': store['locationName'],
                    'addr_full': store['address1'],
                    'city': store['city'],
                    'state': store['state'],
                    'postcode': store.get('zipCode'),
                    'country': store.get('country'),
                    'website': 'https://www.costco.com/warehouse-locations/store-{}.html'.format(ref),
                    'extras': {
                        'number': store["displayName"]
                    }
                }

                hours = store.get('warehouseHours')
                if hours:
                    try:
                        properties["opening_hours"] = self.store_hours(hours)
                    except:
                        pass

                yield GeojsonPointItem(**properties)
