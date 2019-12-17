# -*- coding: utf-8 -*-
"""
Wafflehouse has 1906 locations and connects to a 3rd party end point
https://api.sweetiq.com/store-locator/public/locations/587d236eeb89fb17504336db.
I am guessing 587d236eeb89fb17504336db is what uniquely identifies wafflehouse to this API

The API works by returning locations within a bounding box and there is a perPage URL param
that allows us to specify how many results we need.
When skipped, it returns all.

Widening the box to cover the whole of the United states returned all
1906 results worth 252kb of JSON so we are safe returning all
"""
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class WaffleHouseSpider(scrapy.Spider):
    name = "wafflehouse"
    item_attributes = { 'brand': "Waffle House" }
    allowed_domains = ["sweetiq.com"]
    start_urls = ('https://api.sweetiq.com/store-locator/public/locations/587d236eeb89fb17504336db'
                  '?categories=&geo%5B0%5D=-74.0468&geo%5B1%5D=40.8859&tag=&page=1&'
                  'search=&searchFields%5B0%5D=name&box%5B0%5D=-163.37843921359377&box%5B1%5D=-14.777946567390337&'
                  'box%5B2%5D=-44.198751713593765&box%5B3%5D=70.9012314513329&clientIds%5B0%5D=56fd9c824a88871f1d26062a',)

    def parse(self, response):
        locations = json.loads(response.text)
        if locations['records']:
            for location in locations['records']:
                full_address = location['address'] + " " + location['addressLine2']
                city = location['city']
                state = location['province']
                country = location['country']
                zip_code = location['postalCode']
                latitude = location['geo'][1]
                longitude = location['geo'][0]
                phone = location['phone']
                open_hours = location['hoursOfOperation']
                website = location['website']
                link_id = location['_id']

                properties = {
                    "addr_full": full_address,
                    "city": city,
                    "state": state,
                    "postcode": zip_code,
                    "country": country,
                    "phone": self.process_phone(phone),
                    "website": website,
                    "ref": link_id,
                    "opening_hours": self.process_hours(open_hours),
                    "lon": longitude,
                    "lat": latitude,
                }

                yield GeojsonPointItem(**properties)

    def process_phone(self, phone_number):
        """
        converts phone number from (610) 838-2592 to 610-838-2592
        :param phone_number: the phone number to convert
        :return:
        """
        find_numbers = re.search(r"\((\d{3})\)\s(\d{3})-(\d{4})", phone_number)
        if find_numbers:
            num = find_numbers.groups()
            return num[0] + "-" + num[1] + "-" + num[2]
        else:
            return phone_number

    def process_hours(self, hours):
        """
        Convert a dictionary of hours from
                   'Fri': [['00:00', '23:59']],
                   'Mon': [['00:00', '23:59']],
                   'Sat': [['00:00', '23:59']],
                   'Sun': [['00:00', '23:59']],
                   'Thu': [['00:00', '23:59']],
                   'Tue': [['00:00', '23:59']],
                   'Wed': [['00:00', '23:59']]
        to Mo-Su: 24/7 and handle possible variants
        Wafflehouse is open 24/7 at all locations but if sometime, this changes
        I want to assume this will capture it
        :param hours:
        :return:
        """
        possible_keys = set(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        hours_keys = set([x for x, y in hours.items() if y[0][0] == '00:00' and y[0][1] == '23:59'])
        if possible_keys == hours_keys:
            return 'Mo-Su: 24/7'
        else:
            # if a day is skipped, lets add each day and time independently
            result = []
            for dow, tod in hours.items():
                if tod[0][0] == '00:00' and tod[0][1] == '23:59':
                    # time is 24/7, lets add 24/7 to each
                    # so it looks like Mo 24/7; Tu 24/7 etc.
                    result.append(dow[0:2] + " 24/7")
                else:
                    # if time is not 24/7, lets add actual time
                    result.append(dow[0:2] + " " + tod[0][0] + "-" + tod[0][1])
            if result:
                return "; ".join(result)
        return hours
