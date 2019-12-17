# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


class DollarGeneralSpider(scrapy.Spider):
    name = 'dollar_general'
    item_attributes = { 'brand': "Dollar General" }
    allowed_domains = ['hosted.where2getit.com']

    def start_requests(self):
        url = 'https://hosted.where2getit.com/dollargeneral/rest/locatorsearch?lang=fr_FR'

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            next(points) # Ignore the header
            for point in points:
                row = point.split(',')
                lat = row[1]
                lon = row[2]

                formdata = {
                    "request": {
                        "appkey":"9E9DE426-8151-11E4-AEAC-765055A65BB0",
                        "formdata": {
                            "geoip": "false",
                            "dataview":"store_default",
                            "geolocs": {
                                "geoloc": [
                                    {
                                        "addressline":"",
                                        "country":"US",
                                        "latitude":"{}".format(lat),
                                        "longitude":"{}".format(lon)
                                    }
                                ]
                            },
                            "searchradius":"100",
                            "where": {
                                "nci": {
                                    "eq":""
                                },
                                "or": {
                                    "PROPANE": {
                                        "eq":""
                                    },
                                    "REDBOX": {
                                        "eq":""
                                    },
                                    "RUGDR": {
                                        "eq":""
                                    },
                                    "MULTICULTURAL_HAIR": {
                                        "eq":""
                                    },
                                    "icon": {
                                        "eq":""
                                    },
                                    "DG_GO": {
                                        "eq":""
                                    }
                                }
                            },
                            "false":"0"
                        }
                    }
                }

                headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/json',
                    'Origin': 'https://hosted.where2getit.com',
                    'Host': 'hosted.where2getit.com',
                    'Referer': 'https://hosted.where2getit.com/dollargeneral/',
                    'X-Requested-With': 'XMLHttpRequest'
                }

                yield scrapy.http.Request(
                    url,
                    self.parse,
                    method='POST',
                    body=json.dumps(formdata),
                    headers=headers,
                )

    def parse(self, response):
        result = json.loads(response.body_as_unicode())

        if 'collection' in result['response'].keys():
            for data in result['response']['collection']:
                ref = data['uid']
                lat = data['latitude']
                lon = data['longitude']
                name = data['name']
                state = data['state']
                street = data['address1']
                city = data['city']
                phone = data['phone']
                opening_hours = self.hours(data)
                postalcode = 'postalcode' in data.keys() and re.search(r'\d+', data['postalcode']).group() or ''

                properties = {
                    "phone": phone,
                    "ref": ref,
                    "name": name,
                    "opening_hours": opening_hours,
                    "lat": lat,
                    "lon": lon,
                    "street": street,
                    "city": city,
                    "state": state,
                    "postcode": postalcode
                }

                yield GeojsonPointItem(**properties)

    def hours(self, data):
        hours = []
        for weekday in WEEKDAYS:
            if 'opening_time_' + weekday.lower() in data.keys():
                hours.append('{} {}-{}; '.format(
                    weekday[:2],
                    data['opening_time_' + weekday.lower()],
                    data['closing_time_' + weekday.lower()]
                ))

        return '; '.join(hours)
