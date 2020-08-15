# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS_NAME = {
    'MO': 'Mo',
    'TU': 'Tu',
    'WE': 'We',
    'TH': 'Th',
    'FR': 'Fr',
    'SA': 'Sa',
    'SU': 'Su'
}


class UspsCollectionBoxesSpider(scrapy.Spider):
    name = "usps_collection_boxes"
    item_attributes = { 'brand': "USPS" }
    allowed_domains = ['usps.com']
    download_delay = 0.1

    def start_requests(self):
        url = 'https://tools.usps.com/UspsToolsRestServices/rest/POLocator/findLocations'

        headers = {
            'origin': 'https://tools.usps.com',
            'referer': 'https://tools.usps.com/find-location.htm?',
            'content-type': 'application/json;charset=UTF-8'
        }

        with open('./locations/searchable_points/us_centroids_25mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(',')

                current_state = json.dumps({
                    'requestGPSLat': lat,
                    'requestGPSLng': lon,
                    'maxDistance': '25',
                    'requestType': 'collectionbox',
                })

                yield scrapy.Request(
                    url,
                    method='POST',
                    body=current_state,
                    headers=headers,
                    callback=self.parse,
                )

    def parse_hours(self, hours):
        day_groups = []
        this_day_group = None

        for hour in hours:
            if len(hour["times"]) == 0:
                pass
            else:
                d = hour["dayOfTheWeek"]
                day = DAYS_NAME[d]
                close_time = hour["times"][0]["close"][:-3]

                if not this_day_group:
                    this_day_group = dict(from_day=day, to_day=day, hours=close_time)
                elif this_day_group['hours'] != close_time:
                    day_groups.append(this_day_group)
                    this_day_group = dict(from_day=day, to_day=day, hours=close_time)
                else:
                    this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        collection_times = ""
        for day_group in day_groups:
            if day_group['from_day'] == day_group['to_day']:
                collection_times += '{from_day} {hours}; '.format(**day_group)
            elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                collection_times += '{hours}; '.format(**day_group)
            else:
                collection_times += '{from_day}-{to_day} {hours}; '.format(**day_group)
        collection_times = collection_times[:-2]

        return collection_times

    def parse(self, response):
        stores = json.loads(response.body)

        try:
            stores = stores["locations"]

            for store in stores:
                properties = {
                    'ref': store["locationID"],
                    'name': store["locationName"],
                    'addr_full': store["address1"],
                    'city': store["city"],
                    'state': store["state"],
                    'postcode': store["zip5"],
                    'country': 'US',
                    'lat': store["latitude"],
                    'lon': store["longitude"],
                    'name': store["locationName"],
                    'extras': {
                        'note': store["specialMessage"],
                    }
                }

                try:
                    h = self.parse_hours(store["locationServiceHours"][0]["dailyHoursList"])
                    if h:
                        properties['extras']['collection_hours'] = h
                except:
                    pass

                yield GeojsonPointItem(**properties)
        except:
            pass
