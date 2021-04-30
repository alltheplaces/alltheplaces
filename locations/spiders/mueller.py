import scrapy
import json

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
        weekdays = [d.strip() for d in store_hours.split(',')]
        for record in weekdays:
            day, hours = record.split(' ')
            from_hours, to_hours = hours.split('-')

            opening_hours.add_range(day=DAY_MAPPING[day],
                                    open_time=from_hours,
                                    close_time=to_hours,
                                    time_format='%H:%M'
                                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).get()
        if data:
            properties = {}
            data = json.loads(data)
            for stores in data:
                properties = {
                    'lat': stores['geo']['latitude'],
                    'lon': stores['geo']['longitude'],
                    'name': stores['legalName'],
                    'street': stores['address']['streetAddress'],
                    'city': stores['address']['addressLocality'].replace(
                        ', German', ''
                    ),
                    'postcode': stores['address']['postalCode'],
                    'country': 'DE',
                    'ref': stores['globalLocationNumber'],
                }
                if stores['openingHours']:
                    hours = self.parse_hours(stores['openingHours'])
                    if hours:
                        properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)
