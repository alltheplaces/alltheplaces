# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class PublicStorageSpider(scrapy.Spider):
    name = "public_storage"
    chain_name = "Public Storage"
    allowed_domains = ["www.publicstorage.com"]
    start_urls = (
        'https://www.publicstorage.com/handlers/searchcoordinates.ashx?north=90.0&east=180.0&south=-90.0&west=-180.0',
    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data['response']['properties']['property']:
            lat, lon = map(float, store['lat_long'].split(', '))
            properties = {
                "ref": store.get('property_id'),
                "opening_hours": '; '.join(response.xpath('//time[@itemprop="openingHours"]/@datetime').extract()),
                "addr_full": store.get('address'),
                "city": store.get('city'),
                "state": store.get('state'),
                "postcode": store.get('zip'),
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)
