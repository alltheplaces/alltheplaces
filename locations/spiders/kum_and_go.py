# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class KumAndGoSpider(scrapy.Spider):
    name = "kum_and_go"
    item_attributes = {'brand': "Kum & Go", 'brand_wikidata': "Q6443340"}
    allowed_domains = ["kumandgo.com"]

    def start_requests(self):
        yield scrapy.FormRequest(
            'https://www.kumandgo.com/wordpress/wp-admin/admin-ajax.php',
            method='POST',
            formdata={
                'coords[latitude]': '39.74581290359507',
                'coords[longitude]': '-104.96756559990148',
                'radius': '3000',
                'action': 'stores_coords'
            })

    def parse(self, response):
        result = json.loads(response.body_as_unicode())
        for store in result['data']['stores']:
            opening_hours = OpeningHours()

            for hours_key in [
                'monday_hours',
                'tuesday_hours',
                'wednesday_hours',
                'thursday_hours',
                'friday_hours',
                'saturday_hours',
                'sunday_hours'
            ]:
                (open_time, close_time) = store[hours_key].split(' - ')

                opening_hours.add_range(day=hours_key[:2].capitalize(),
                                        open_time=open_time,
                                        close_time=close_time,
                                        time_format='%I:%M %p')

            yield GeojsonPointItem(
                ref=store['store_id'],
                lon=store['longitude'],
                lat=store['latitude'],
                name=store['name'],
                addr_full=store['address1'],
                city=store['city'],
                state=store['state'],
                postcode=store['postalcode'],
                country=store['country'],
                phone=store['phone'],
                website=store['url'],
                opening_hours=opening_hours.as_opening_hours(),
                extras={
                    'amenity:fuel': True,
                    'atm': int(store['atm'] or 0) == 1,
                    'car_wash': int(store['car_wash'] or 0) == 1,
                    'fuel:diesel': int(store['diesel'] or 0) == 1,
                    'fuel:e85': int(store['e85'] or 0) == 1,
                    'hgv': int(store['semi_truck_fuel_island'] or 0) == 1,
                }
            )
