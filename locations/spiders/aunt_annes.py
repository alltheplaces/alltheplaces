# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from urllib.parse import urlencode

BASE_URL = 'https://www.auntieannes.com/Location/Map/Get?'

DAY_MAPPING = {'Monday': 'Mo',
               'Tuesday': 'Tu',
               'Wednesday': 'We',
               'Thursday': 'Th',
               'Friday': 'Fr',
               'Saturday': 'Sa',
               'Sunday': 'Su'}


class AuntieAnnesSpider(scrapy.Spider):
    name = "auntie_annes"
    brand = "Auntie Anne's"
    allowed_domains = ["www.auntieannes.com"]
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in DAY_MAPPING:
            day = store_day[:2]
            open_close = store_hours.get(store_day)
            if open_close is None or open_close == 'closed':
                continue
            if open_close == 'open24':
                open_time = '00:00'
                close_time = '23:59'
            else:
                open_time, close_time = open_close.split('-')
            opening_hours.add_range(day=day,
                                    open_time=open_time,
                                    close_time=close_time,
                                    time_format='%H:%M'
                                    )

        return opening_hours.as_opening_hours()

    def start_requests(self):
        url = BASE_URL

        with open('./locations/searchable_points/us_centroids_25mile_radius.csv') as points:

            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(',')

                params = {
                    'brand': '{DBEA0CF2-5A2E-4487-8A9B-504E8E147D13}',
                    'addressLatitude': '{}'.format(lat),
                    'addressLongitude': '{}'.format(lon),
                }

                yield scrapy.http.Request(url + urlencode(params), callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data["Locations"]

        for store in stores:

            properties = {
                'name': store["LocationName"],
                'ref': store["StoreNumber"],
                'addr_full': store["StreetAddress"],
                'city': store["Locality"],
                'state': store["Region"],
                'postcode': store["PostalCode"],
                'country': store["CountryName"],
                'phone': store.get("Tel"),
                'website': store.get("Website") or response.url,
                'lat': store.get("Latitude"),
                'lon': store.get("Longitude"),
                'extras': {
                    'food_truck': store.get("FoodTruck")
                }
            }

            hours = self.parse_hours(store.get("Hours"))
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
