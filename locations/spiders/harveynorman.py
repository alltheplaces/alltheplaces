# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

class HarveyNormanSpider(scrapy.Spider):
    #download_delay = 0.3
    name = "harvey_norman"
    item_attributes = {'brand': "harvey_normal"}
    allowed_domains = ["harvey-norman-au.locally.com"]
    start_urls = ([
        'https://harvey-norman-au.locally.com/stores/conversion_data?has_data=true&company_id=143426&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=-31.526082580069342&map_center_lng=143.58341849734816&map_distance_diag=2726.929242626677&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=4&lang=en-us',
    ])

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data['markers']:
            properties = {
                'ref': i['id'],
                'name': i['name'],
                'addr_full': i['address'],
                'city': i['city'],
                'state': i['state'],
                'postcode': i['zip'],
                'country': i['country'],
                'phone': i['phone'],
                'lat': float(i['lat']),
                'lon': float(i['lng']),
            }
            yield GeojsonPointItem(**properties)