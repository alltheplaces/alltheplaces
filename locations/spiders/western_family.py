# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class WesternFamilySpider(scrapy.Spider):

    name = "western_family"
    item_attributes = { 'brand': "Western Family" }
    allowed_domains = ["www.westernfamily.com"]
    start_urls = (
        'http://www.westernfamily.com/wp-admin/admin-ajax.php?action=store_search&lat=45.5230622&lng=-122.67648159999999&max_results=2500&search_radius=50000&autoload=1',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results:
            properties = {
                'ref': data['id'],
                'name': data['store'],
                'lat': data['lat'],
                'lon': data['lng'],
                'addr_full': data['address'],
                'city': data['city'],
                'state': data['state'],
                'postcode': data['zip'],
                'country': data['country'],
                'phone': data['phone'],
                'website': data['url'],
            }

            yield GeojsonPointItem(**properties)
