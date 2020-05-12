# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class ShellSpider(scrapy.Spider):
    name = "shell"
    item_attributes = {'brand': "Shell", 'brand_wikidata': "Q154950"}
    allowed_domains = ["shellgsllocator.geoapp.me"]
    download_delay = 0.2
    start_urls = [
        "https://shellgsllocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D=-90&sw%5B%5D=-180&ne%5B%5D=90&ne%5B%5D=180"
    ]

    def parse(self, response):
        for result in json.loads(response.body_as_unicode()):
            # This within_bounds endpoint always returns an array with one of
            # two kinds of response.
            #
            # 1. An array of smaller bounding boxes with counts
            # 2. An array of station listings
            if 'bounds' in result:
                b = result['bounds']

                yield scrapy.Request(
                    f"https://shellgsllocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D={b['sw'][0]}&sw%5B%5D={b['sw'][1]}&ne%5B%5D={b['ne'][0]}&ne%5B%5D={b['ne'][1]}"
                )
            if 'name' in result:
                if result['inactive']:
                    continue

                yield GeojsonPointItem(
                    lat=result['lat'],
                    lon=result['lng'],
                    name=result['name'],
                    addr_full=result['address'],
                    city=result['city'],
                    state=result['state'],
                    postcode=result['postcode'],
                    country=result['country_code'],
                    phone=result['telephone'],
                    website=result['website_url'],
                    ref=result['id'],
                    extras={
                        'amenity': 'fuel',
                        'amenities': result['amenities']
                    }
                )
