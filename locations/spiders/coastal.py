# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class CoastalFarmSpider(scrapy.Spider):

    name = "coastalfarm"
    allowed_domains = ["www.coastalfarm.com"]
    start_urls = (
        'https://www.coastalfarm.com/wp-admin/admin-ajax.php?action=store_search&lat=45.523062&lng=-122.67648199999996&max_results=25&search_radius=50',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        print(results)
        for data in results:
            properties = {
                'city': data['city'],
                'ref': data['id'],
                'lon': data['lng'],
                'lat': data['lat'],
                'addr_full': data['address'],
                'phone': data['phone'],
                'state': data['state'],
                'postcode': data['zip'],
                'website': data['url']
            }

            yield GeojsonPointItem(**properties)

