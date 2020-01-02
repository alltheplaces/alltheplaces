# -*- coding: utf-8 -*-
import re
import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from urllib.parse import urlencode

DAY_MAPPING = {'1': 'Mo', '2': 'Tu', '3': 'We', '4': 'Th',
               '5': 'Fr', '6': 'Sa', '7': 'Su'}


class CricketWirelessSpider(scrapy.Spider):
    download_delay = 0.2
    name = "cricket_wireless"
    item_attributes = {'brand': "Cricket Wireless"}
    allowed_domains = ["momentfeed-prod.apigee.net"]

    def start_requests(self):
        with open('./locations/searchable_points/us_centroids_25mile_radius.csv') as points:
            next(points)  # Ignore the header
            for point in points:
                row = point.split(',')
                lat = row[1]
                lon = row[2]

                # Page size appears capped at 100.  Even if pageSize querystring parameter is set to a value >100,
                # only seeing up to 100 stores in the response.
                #
                # Was not able to get additional pages of values by setting page to value >1.  So use a relatively
                # small searchable grid w/ 25 mile radius.  We are unlikely to find more than 100 stores within that
                # radius.
                #
                # An alternative may be to crawl the site directory rooted at:
                # https://www.cricketwireless.com/stores/site-map , but
                #
                # 1) The request count is not reduced much (There are 4,995 US stores listed in the site directory,
                #    compared to 5,867 centroids in the 25mi US list).
                # 2) The centroid search reveals some stores not yet added to the site directory.
                #
                url = f'https://momentfeed-prod.apigee.net/api/llp/cricket.json?auth_token=IVNLPNUOBXFPALWE&center={lat},{lon}&coordinates=-64.16810689799152,0.87890625,80.70399666821143,-164.1796875&multi_account=false&name=Cricket+Wireless+Authorized+Retailer,Cricket+Wireless+Store&page=1&pageSize=100&type=store'

                headers = {
                    'Accept': 'application/json, text/javascript, */*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Host': 'momentfeed-prod.apigee.net'
                }

                yield scrapy.http.Request(
                    url,
                    self.parse,
                    method='GET',
                    headers=headers
                )

    def parse(self, response):
        store_data = json.loads(response.body_as_unicode())

        # Searches without a store return a dict with a message, otherwise a list of stores as json arrays
        if isinstance(store_data, list):

            for store in store_data:

                properties = {
                    'addr_full': store["store_info"]["address"],
                    'city': store["store_info"]["locality"],
                    'state': store["store_info"]["region"],
                    'postcode': store["store_info"]["postcode"],
                    'country': store["store_info"]["country"],
                    'ref': store["store_info"]["corporate_id"],
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

                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time=open_time[0:2]+":"+open_time[2:4],
                                        close_time="23:59" if (close_time[0:2]+":"+close_time[2:4]) == "24:00" else close_time[0:2]+":"+close_time[2:4])

            return opening_hours.as_opening_hours()
