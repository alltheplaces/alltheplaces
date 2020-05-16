import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class TexasRoadhouseSpider(scrapy.Spider):
    name = "texas_roadhouse"
    item_attributes = { 'brand': "Texas Roadhouse", 'brand_wikidata': "Q7707945" }
    allowed_domains = ["www.texasroadhouse.com"]
    start_urls = (
        'https://www.texasroadhouse.com/locations',
    )

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            # convert day from full Monday to Mo, etc
            day = weekday.get('day')[:2]
            open_time = weekday.get('hours').get('open')
            close_time = weekday.get('hours').get('close')
            opening_hours.add_range(day=day,
                                    open_time=open_time,
                                    close_time=close_time,
                                    time_format='%I:%M%p')

        return opening_hours.as_opening_hours()

    def parse(self, response):
        script_content = response.xpath('//script[contains(text(),"__locations__")]/text()').extract_first()
        # effectively strip off leading "window.__locations__ = " where
        # the rest is a json blob
        script_data = script_content.split(" = ", 1)[-1]
        script_data = script_data.rstrip(";")
        stores = json.loads(script_data)

        for store in stores:
            properties = {
                'lat': store['gps_lat'],
                'lon': store['gps_lon'],
                'ref': store['url'],
                'addr_full': store['address1'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['zip'],
                'country': store['country'],
                'phone': store['phone'],
                'website': response.urljoin(store['url']),
                'opening_hours': self.parse_hours(store['schedule']),
                'extras': {
                    'amenity:toilets': True,
                },
            }

            yield GeojsonPointItem(**properties)
