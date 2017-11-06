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

    def address(self, address):
        if not address:
            return None

        (num, rest) = address['address1'].split(' ', 1)
        addr_tags = {
            "addr:housenumber": num.strip(),
            "addr:street": rest.strip(),
            "addr:city": address['city'],
            "addr:state": address['state'],
            "addr:postcode": address['postalCode'],
        }

        return addr_tags

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

            properties = {
                "ref": str(store['id']),
                "phone": store.get('phone'),
                "name": store['storeType']['name'],
            }

            opening_hours = self.store_hours(store['operationalHours'])
            if opening_hours:
                properties['opening_hours'] = opening_hours

            open_date = store.get('openDate')
            if open_date:
                properties['start_date'] = '{}-{}-{}'.format(
                    open_date[6:10],
                    open_date[0:2],
                    open_date[3:5],
                )

            address = self.address(store['address'])
            if address:
                properties.update(address)

            lon_lat = [
                store['geoPoint']['longitude'],
                store['geoPoint']['latitude'],
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )

            yield scrapy.Request(
                'http://www.walmart.com/store/ajax/detail-navigation?location={}'.format(
                    store['address']['postalCode']
                ),
            )
