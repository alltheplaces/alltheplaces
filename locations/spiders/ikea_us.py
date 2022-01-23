# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su',
}


class IkeaUSSpider(scrapy.Spider):
    name = "ikea_us"
    item_attributes = {'brand': "Ikea"}
    allowed_domains = ["ikea.com"]
    start_urls = (
        'https://ww8.ikea.com/ext/iplugins/v2/en_US/data/localstorefinder/data.json',
    )

    def store_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            opening_hours.add_range(day=DAY_MAPPING[weekday['day']],
                                    open_time=':'.join([weekday['openHours'], weekday['openMinutes']]),
                                    close_time=':'.join([weekday['closeHours'], weekday['closeMinutes']]),
                                    time_format='%I:%M')

        return opening_hours.as_opening_hours()

    def parse(self, response):
        store_data = json.loads(response.text)

        for store in store_data:

            properties = {
                'name': store["storeCity"],
                'ref': store["storeNumber"] or store["storeId"],
                'addr_full': store["storeAddress"],
                'city': store["storeCity"],
                'state': store["storeState"],
                'postcode': store["storeZip"],
                'country': "US",
                'website': store.get("storeURL"),
                'lat': float(store["geoLat"]),
                'lon': float(store["geoLng"]),
            }

            hours = store["storeHours"]
            if hours:
                properties["opening_hours"] = self.store_hours(hours)

            yield GeojsonPointItem(**properties)
