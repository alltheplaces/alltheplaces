import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {'MONDAY': 'Mo',
               'TUESDAY': 'Tu',
               'WEDNESDAY': 'We',
               'THURSDAY': 'Th',
               'FRIDAY': 'Fr',
               'SATURDAY': 'Sa',
               'SUNDAY': 'Su'}

class MuellerSpider(scrapy.Spider):
    name = "mueller"
    allowed_domains = ["www.mueller.de"]
    start_urls = (
        'https://www.mueller.de/meine-filiale/',
    )
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("dayOfWeek")]
            open_time = store_day.get("fromTime")
            close_time = store_day.get("toTime")
            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(day=day,
                                    open_time=open_time,
                                    close_time=close_time,
                                    time_format='%H:%M'
                                    )

        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        stores = json.loads(response.body_as_unicode())
        properties = {
            'lat': stores['latitude'],
            'lon': stores['longitude'],
            'name': stores['companyName'],
            'street': stores['street'],
            'city': stores['city'],
            'postcode': stores['zip'],
            'country': stores['country'],
            'phone': stores['ccstoreDtoDetails']['phone'],
            'ref': stores['storeNumber'],
        }
        hours = self.parse_hours(stores['ccstoreDtoDetails']['openingHourWeek'])

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        store_numbers = re.findall(r'{storeNumber: \'(\d+)\'', response.text)
        if store_numbers:
            for n in store_numbers:
                yield scrapy.Request(
                    url="https://www.mueller.de/api/ccstore/byStoreNumber/{}/".format(n),
                    callback=self.parse_details
                )

