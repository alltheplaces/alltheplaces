# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


STATES = [
    'AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FM', 'FL',
    'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MH',
    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM',
    'NY', 'NC', 'ND', 'MP', 'OH', 'OK', 'OR', 'PW', 'PA', 'PR', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV', 'WI', 'WY'
]

DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}

class JiffyLubeSpider(scrapy.Spider):
    name = "jiffylube"
    item_attributes = {'brand': "Jiffy Lube"}
    allowed_domains = ["www.jiffylube.com"]

    def start_requests(self):
        template = 'https://www.jiffylube.com/api/locations?state={state}'

        headers = {
            'Accept': 'application/json',
        }

        for state in STATES:
            yield scrapy.http.FormRequest(
                url=template.format(state=state),
                method='GET',
                headers=headers,
                callback=self.parse
            )
    def parse(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        for stores in jsonresponse:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                'name': store_data["nickname"],
                'ref': store_data["id"],
                'addr_full': store_data["address"],
                'city': store_data["city"],
                'state': store_data["state"],
                'postcode': store_data["postal_code"].strip(),
                'country': store_data["country"],
                'phone': store_data["phone_main"],
                'lat': float(store_data["coordinates"]["latitude"]),
                'lon': float(store_data["coordinates"]["longitude"]),
                'website': "https://www.jiffylube.com{}".format(store_data["_links"]["_self"])
            }

            hours = store_data["hours_schema"]

            if hours:
                properties['opening_hours'] = self.process_hours(hours)

            yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["name"]
            open_time = hour["time_open"]
            close_time = hour["time_close"]

            opening_hours.add_range(day=DAY_MAPPING[day], open_time=open_time, close_time=close_time,
                                    time_format='%H:%M')
        return opening_hours.as_opening_hours()