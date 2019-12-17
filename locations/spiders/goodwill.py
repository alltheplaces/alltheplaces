# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

CATEGORY_MAPPING = {
    '1': 'Donation Site',
    '2': 'Outlet',
    '3': 'Retail Store',
    '4': 'Job & Career Support',
    '5': 'Headquarters'
}


class GoodwillSpider(scrapy.Spider):
    name = "goodwill"
    chain_name = "Goodwill"
    allowed_domains = ['www.goodwill.org']
    download_delay = 0.2

    def start_requests(self):
        url = 'https://www.goodwill.org/getLocations.php'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        with open('./locations/searchable_points/us_centroids_25mile_radius.csv') as points:

            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(',')

                # Unable to find a way to specify a search radius
                # Appears to use a set search radius somewhere > 25mi, using 25mi to be safe
                form_data = {
                    'lat': '{}'.format(lat),
                    'lng': '{}'.format(lon),
                    'cats': '3,1,2,4,5'  # Includes donation sites
                }

                yield scrapy.http.FormRequest(url=url, method='POST', formdata=form_data, headers=headers,
                                              callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data:
            service_codes = store.get("services")

            store_categories = []
            for code in service_codes:
                store_categories.append(CATEGORY_MAPPING[code])

            properties = {
                'name': store["name"],
                'ref': store["id"],
                'addr_full': store["address1"],
                'city': store["city"],
                'state': store["state"],
                'postcode': store["postal_code"],
                'country': store["country"],
                'phone': store.get("phone"),
                'website': store.get("website") or response.url,
                'lat': store.get("lat"),
                'lon': store.get("lng"),
                'extras': {
                    'service_codes': service_codes,
                    'store_categories': store_categories
                }
            }

            yield GeojsonPointItem(**properties)
