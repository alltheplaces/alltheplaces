import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    1: 'Mo',
    2: 'Tu',
    3: 'We',
    4: 'Th',
    5: 'Fr',
    6: 'Sa',
    7: 'Su'
}

COUNTRY_MAPPING = {
    'DE': 'Germany',
    'AT': 'Austria',
    'CZ': 'Czech Republic'
}

class DmSpider(scrapy.Spider):
    name = "dm"
    allowed_domains = ["services.dm.de"]
    start_urls = (
        'https://services.dm.de/storedata/stores/bbox/85.999%2C-179.999%2C-89.999%2C179.999/cluster/zip',
    )
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("weekDay")]
            open_time = store_day['timeSlices'][0]['opening']
            close_time = store_day['timeSlices'][0]['closing']
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
        for store in stores['stores']:
            if store['localeCountry'] in COUNTRY_MAPPING:
                properties = {
                    'country': COUNTRY_MAPPING[store['localeCountry']],
                    'ref': store['storeNumber'],
                    'phone': store['phone'],
                    'name': store['address']['name'],
                    'street': store['address']['street'],
                    'postcode': store['address']['zip'],
                    'city': store['address']['city'],
                    'lat': store['location']['lat'],
                    'lon': store['location']['lon'],
                }
                hours = self.parse_hours(store['openingDays'])

                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)

    def parse(self, response):
        locations = json.loads(response.body_as_unicode())
        for l in locations:
            lat = locations[l]['centerPoint']['lat']
            lon = locations[l]['centerPoint']['lon']
            lat_1 = lat + 2.56
            lat_2 = lat - 2.56
            lon_1 = lon + 8
            lon_2 = lon - 8

            url = "https://services.dm.de/storedata/stores/bbox/{}%2C{}%2C{}%2C{}".format(lat_1, lat_2, lon_2, lon_1)

            yield scrapy.Request(
                url=url,
                callback=self.parse_details
            )
