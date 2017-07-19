# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class PublicStorageSpider(scrapy.Spider):
    name = "public_storage"
    allowed_domains = ["www.publicstorage.com"]
    start_urls = (
        'https://www.publicstorage.com/handlers/searchcoordinates.ashx?north=90.0&east=180.0&south=-90.0&west=-180.0',
    )

    def address(self, store):
        addr_tags = {
            "addr:full": store.get('address'),
            "addr:city": store.get('city'),
            "addr:state": store.get('state'),
            "addr:postcode": store.get('zip'),
        }

        return addr_tags

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data['response']['properties']['property']:
            yield scrapy.Request(
                'https://www.publicstorage.com/storage-location-details-modal.aspx?site_id={}&property_id={}'.format(
                    store['site_id'],
                    store['property_id'],
                ),
                meta=store,
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "ref": response.meta.get('property_id'),
            "opening_hours": '; '.join(response.xpath('//time[@itemprop="openingHours"]/@datetime').extract())
        }

        address = self.address(response.meta)
        if address:
            properties.update(address)

        lat, lon = map(float, response.meta['lat_long'].split(', '))
        lon_lat = [
            lon,
            lat,
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
