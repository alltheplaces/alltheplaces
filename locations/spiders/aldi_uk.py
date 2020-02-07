# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class AldiUkSpider(scrapy.Spider):
    name = "aldiuk"
    item_attributes = { 'brand': "Aldi" }
    allowed_domains = ['www.aldi.co.uk']
    start_urls = (
        'https://www.aldi.co.uk/sitemap.xml',
    )

    # Extracts store's data from an individual store page
    def parse_store_page(self, response):
        response.selector.remove_namespaces()

        # Get a JS object with all store information
        store = json.loads( response.css('.js-store-finder-initial-state').xpath('./text()').get() )['store']

        # Transform an array of objects for opening times into a string
        hours = [ '{} {}'.format(d['day'], d['hours'].replace('&nbsp;&ndash;&nbsp;', '-')) for d in store['openingTimes'] ]
        hours_str = '; '.join(hours)

        # Address = Street (sometimes with Number) extracted from title, together with Address array from data object
        street_full = store['name'].split('ALDI - ')[1].strip()
        addr_full = '{}, {}'.format(street_full, ', '.join(store['address']))

        # From ALDI's name, extract housenumber & street name
        addr_regex = r"^(Unit\s.|\d*\-?\d*),?\s?(.*)$"
        housenumber = re.search(addr_regex, street_full).group(1)
        street =  re.search(addr_regex, street_full).group(2)

        properties = {
            'name': store['name'],
            'ref': store['code'],
            'website': 'https://www.aldi.co.uk/store/{}'.format(store['code']),
            'lat': float( store['latlng']['lat'] ),
            'lon': float( store['latlng']['lng'] ),
            'postcode': store['address'][-1],
            'city': store['address'][-2],
            'addr_full': addr_full,
            'opening_hours': hours_str,
            'street': street,
            'housenumber': housenumber,
            'country': 'UK',
        }

        yield GeojsonPointItem(**properties)


    # Extracts URLs for all individual stores from the XML document
    def parse_stores(self, response):
        response.selector.remove_namespaces()

        for url in response.xpath('//url'):
            yield scrapy.Request( url.xpath('.//loc/text()').get(), callback=self.parse_store_page )


    # Start by parsing the Sitemap: find a page with URLs of all Aldi UK stores
    def parse(self, response):
        response.selector.remove_namespaces()

        for sitemap_item in response.xpath('//sitemap'):
            sitemap_item_url = sitemap_item.xpath('.//loc/text()').get()

            if '/store-' in sitemap_item_url:
                yield scrapy.Request( sitemap_item_url , callback=self.parse_stores)