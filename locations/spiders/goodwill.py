# -*- coding: utf-8 -*-
import csv
import json
import scrapy
from locations.items import GeojsonPointItem
from urllib.parse import urlencode

CATEGORY_MAPPING = {
    '1': 'Donation Site',
    '2': 'Outlet',
    '3': 'Retail Store',
    '4': 'Job & Career Support',
    '5': 'Headquarters'
}


class GoodwillSpider(scrapy.Spider):
    name = "goodwill"
    item_attributes = {'brand': "Goodwill", 'brand_wikidata': "Q5583655"}
    allowed_domains = ['www.goodwill.org']
    download_delay = 0.2

    def start_requests(self):
        with open('./locations/searchable_points/us_centroids_25mile_radius.csv') as points:
            reader = csv.DictReader(points)
            for point in reader:
                # Unable to find a way to specify a search radius
                # Appears to use a set search radius somewhere > 25mi, using 25mi to be safe
                params = {
                    'lat': point['latitude'],
                    'lng': point['longitude'],
                    'cats': '3,1,2,4,5'  # Includes donation sites
                }

                url = 'https://www.goodwill.org/GetLocAPI.php?' + urlencode(params)
                self.logger.error(url)
                yield scrapy.Request(url=url)

    def parse(self, response):
        data = json.loads(response.text)

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
