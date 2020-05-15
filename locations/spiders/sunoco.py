# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SunocoSpider(scrapy.Spider):
    name = "sunoco"
    item_attributes = {'brand': "Sunoco", 'brand_wikidata': "Q1423218"}
    allowed_domains = ["sunoco.com"]

    start_urls = ['https://www.sunoco.com/js/locations.json']

    def parse(self, response):
        for location in json.loads(response.body_as_unicode()):
            opening_hours = OpeningHours()

            for key in [
                'Hrs of Operation Mon-Sat Open',
                'Hrs of Operation Mon-Sat Close',
                'Hrs of Operation Sun Open',
                'Hrs of Operation Sun Close'
            ]:
                if location[key] >= 2400:
                    location[key] -= 2400

            for day in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']:
                opening_hours.add_range(day=day,
                                        open_time=f"{location['Hrs of Operation Mon-Sat Open']:04d}",
                                        close_time=f"{location['Hrs of Operation Mon-Sat Close']:04d}",
                                        time_format='%H%M')

            opening_hours.add_range(day='Su',
                                    open_time=f"{location['Hrs of Operation Sun Open']:04d}",
                                    close_time=f"{location['Hrs of Operation Sun Close']:04d}",
                                    time_format='%H%M')

            yield GeojsonPointItem(
                ref=location['Facility ID'],
                lon=location['Longitude'],
                lat=location['Latitude'],
                # name as shown on the Sunoco site
                name=f"Sunoco #{location['Facility ID']}",
                addr_full=location['Address'],
                city=location['City'],
                state=location['State'],
                postcode=location['Zip'],
                country='US',
                phone=location['Phone'],
                opening_hours=opening_hours.as_opening_hours(),
                extras={
                    'amenity:fuel': True,
                    'atm': int(location['ATM'] or 0) == 1,
                    'car_wash': int(location['Car Wash'] or 0) == 1,
                    'fuel:diesel': int(location['Diesel'] or 0) == 1,
                    'fuel:kerosene': int(location['Kerosene'] or 0) == 1
                }
            )
