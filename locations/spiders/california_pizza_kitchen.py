# -*- coding: utf-8 -*-
import datetime
import re
import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

days = {'1': 'Mo','2': 'Tu','3': 'We','4': 'Th',
            '5': 'Fr','6': 'Sa','7': 'Su'}

class cpkSpider(scrapy.Spider):
    download_delay = 0.2
    name = "cpk"
    allowed_domains = ["momentfeed-prod.apigee.net"]
    start_urls = (
        'https://momentfeed-prod.apigee.net/api/llp.json?auth_token=CYQKJJAYDMERQLLE&country=US&region=AL&pageSize=1000',
    )

    def start_requests(self):

        base_url = 'https://momentfeed-prod.apigee.net/api/llp.json?auth_token=CYQKJJAYDMERQLLE&country=US&region={}&pageSize=1000'

        for state in states:
            state_url = base_url.format(state)
            request = scrapy.Request(state_url,callback = self.parse)
            yield request

    def parse(self, response):
        jsonresponse = json.loads(response.body_as_unicode())

        # States without a store return a dict with a message, otherwise a list of stores as json arrays
        if isinstance(jsonresponse, list):

            for store in jsonresponse:
                ref = re.search(r'.+/(.+)', store["store_info"]["website"]).group(1)

                properties = {
                    'addr_full': store["store_info"]["address"],
                    'city': store["store_info"]["locality"],
                    'state': store["store_info"]["region"],
                    'postcode': store["store_info"]["postcode"],
                    'country': store["store_info"]["country"],
                    'ref': ref,
                    'website': store["store_info"]["website"],
                    'lat': store["store_info"]["latitude"],
                    'lon': store["store_info"]["longitude"],
                    'name': store["store_info"]["name"]
                }

                store_hours = self.parse_hours(store["store_info"]["store_hours"])

                if store_hours:
                    properties['opening_hours'] = store_hours

                yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):

        if hours != '':

            opening_hours = OpeningHours()

            hour_list = hours.strip(";").split(";")

            for hour in hour_list:
                day, open_time, close_time = re.search(
                    '(.),(.+),(.+)', hour).groups()

                opening_hours.add_range(day = days[day],
                                        open_time = open_time[0:2]+":"+open_time[2:4],
                                        close_time = "23:59" if (close_time[0:2]+":"+close_time[2:4]) == "24:00" else close_time[0:2]+":"+close_time[2:4])

            return opening_hours.as_opening_hours()
