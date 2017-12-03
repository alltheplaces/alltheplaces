# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class WalmartSpider(scrapy.Spider):
    name = "walmart"
    allowed_domains = ["walmart.com"]
    start_urls = (
        'http://www.walmart.com/store/ajax/detail-navigation?location=24019',
        'http://www.walmart.com/store/ajax/detail-navigation?location=98101',
    )

    def store_hours(self, store_hours):
        if store_hours.get('open24Hours'):
            return u'24/7'
        elif store_hours.get('empty'):
            return None
        else:
            combined = store_hours.get('operationalHoursCombined')

            opening_hours = ""
            if len(combined) == 1 \
              and combined[0]['dailyHours']['dayConstant'] == 1 \
              and combined[0]['dailyHours']['endDayConstant'] == 7:
                opening_hours = "{}-{}".format(
                    combined[0]['dailyHours']['startHr'],
                    combined[0]['dailyHours']['endHr'].replace('24:', '00:'),
                )
            else:
                for r in combined:
                    if not r['dailyHours'].get('startHr'):
                        continue

                    day_group = "{} {}-{}; ".format(
                        r['dayNameShort'].replace(' ', ''),
                        r['dailyHours']['startHr'],
                        r['dailyHours']['endHr'].replace('24:', '00:'),
                    )

                    opening_hours += day_group
                opening_hours = opening_hours[:-2]
            return opening_hours

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        if data['status'] == 'error':
            raise Exception("Error: " + data['message'])

        stores = data['payload']['stores']

        for store in stores:
            open_date = store.get('openDate')
            if open_date:
                open_date = '{}-{}-{}'.format(
                    open_date[6:10],
                    open_date[0:2],
                    open_date[3:5],
                )

            yield GeojsonPointItem(
                lat=store['geoPoint']['latitude'],
                lon=store['geoPoint']['longitude'],
                ref=str(store['id']),
                phone=store.get('phone'),
                name=store['storeType']['name'],
                opening_hours=self.store_hours(store['operationalHours']),
                addr_full=store.get('address', {}).get('address1'),
                city=store.get('address', {}).get('city'),
                state=store.get('address', {}).get('state'),
                postcode=store.get('address', {}).get('postalCode'),
                extras={
                    'start_date': open_date
                }
            )

            yield scrapy.Request(
                'http://www.walmart.com/store/ajax/detail-navigation?location={}'.format(
                    store['address']['postalCode']
                ),
            )
