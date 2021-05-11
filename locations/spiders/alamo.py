# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem


class AlamoSpider(scrapy.Spider):
    name = "alamo"
    allowed_domains = ["alamo.com"]


    def start_requests(self):
        base_url = 'https://search.location.enterprise.com/v1/search/location/alamo/web/spatial?includePartnerBranches=false&latitude={lat}&longitude={lng}&radius=250'

        headers={
            "x-api-key": "ASO1Cjq4Of6JVa1N4lJYg3YUn9gPky4S2IpxGjMj"
        }

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            for point in points:
                _, lat, lon = point.strip().split(',')
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(
                    url=url,
                    headers=headers,
                    callback=self.parse
                    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        loc_data = (data["result"])

        for loc in loc_data:

            properties = {
                'name': loc["name"],
                'brand': loc["brand"],
                'phone': loc["phones"][0],
                'addr_full': loc["address"]["street_addresses"],
                'city': loc["address"]["city"],
                'state': loc["address"]["country_subdivision_code"],
                'postcode': loc["address"]["postal"],
                'country': loc["address"]["country_code"],
                'lat': float(loc["gps"]["latitude"]),
                'lon': float(loc["gps"]["longitude"]),
                'ref': loc["id"],
            }

            yield GeojsonPointItem(**properties)
