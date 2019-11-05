# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem
from urllib.parse import urlencode

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

BASE_URL = 'https://local.fedex.com/'


class FedExOfficeSpider(scrapy.Spider):
    name = "fedex_office"
    allowed_domains = ['fedex.com']
    download_delay = 0.2
    start_urls = [
        'https://local.fedex.com/',
    ]

    def parse(self, response):
        for state in STATES:
            url = BASE_URL + state.lower() + '/a/'
            yield scrapy.Request(url, callback=self.parse_locations_by_letter)

    def parse_locations_by_letter(self, response):
        # Does not include urls to the "a" page, will need a separate request for each "state/a" page
        letter_urls = response.xpath('//div[@class="loc-state-letters fx-cf"]/ul/li//@href').extract()

        for letter_url in letter_urls:
            yield scrapy.Request(response.urljoin(letter_url), callback=self.parse_cities)

        yield scrapy.Request(response.url, callback=self.parse_cities)  # parse "a" cities too

    def parse_cities(self, response):
        city_urls = response.xpath('//ul[@class="loc-state-cities loc-simple-column"]/li//@href').extract()

        for city_url in city_urls:
            # Filter response to store locations, exclude drop boxes
            params = {
                'ajax': 'true',
                'group_filters[]': 'office_group',
                'filters[]': 'office',  # FedEx Office Print & Ship Center
                'filters[]': 'officesc',  # FedEx Office Ship Center
                'filters[]': 'officescu',  # FedEx Office Hotel/Convention Center
                'filters[]': 'officeun',  # FedEx Office University Center
                'filters[]': 'walmart',  # FedEx Office Inside Walmart
                'filters[]': 'freight',  # FedEx Freight
                'filters[]': 'fedex',  # FedEx Ship Center
                'show': '50'  # Max number of results allowed
            }

            yield scrapy.http.Request('?'.join([response.urljoin(city_url), urlencode(params)]),
                                      callback=self.parse_stores)

    def parse_stores(self, response):
        # Handle bad links e.g. RI - Pereira is not a valid store page, redirects to state page
        try:
            # If a valid store page
            data = json.loads(response.body_as_unicode())
        except json.decoder.JSONDecodeError:
            # If not a valid page
            return

        stores = data["results"]  # only includes store hours for the day request was made
        for store in stores:
            properties = {
                'name': store["disp_nm"],
                'ref': store["locid"],
                'addr_full': store["address"],
                'city': store["city"],
                'state': store["state"],
                'postcode': store["postalcode"],
                'country': store["country_cd"],
                'phone': store.get("stor_phone"),
                'website': store.get("location_url") or response.url,
                'lat': store.get("latitude"),
                'lon': store.get("longitude"),
                'extras': {
                    'branch_id': store.get("fxo_branch_id"),
                    'location_code': store.get("local_fdx_type"),
                    'location_type': store.get("location_type"),
                    'venue': store.get("bldg"),
                    'venue_note': store.get("loc_onprop")
                }
            }

            yield GeojsonPointItem(**properties)
