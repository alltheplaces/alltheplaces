# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class SuperAmericaSpider(scrapy.Spider):
    name = "speedway"
    allowed_domains = ["www.speedway.com"]
    start_urls = (
        'https://www.speedway.com/GasPriceSearch',
    )

    def parse(self, response):
        yield scrapy.Request(
            'https://www.speedway.com/Services/StoreService.svc/getstoresbyproximity',
            callback=self.parse_search,
            method='POST',
            body='{"latitude":45.0,"longitude":-90.0,"radius":-1,"limit":0}',
            headers={
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json',
            }
        )

    def parse_search(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data:
            yield GeojsonPointItem(
                addr_full=store['address'],
                city=store['city'],
                state=store['state'],
                postcode=store['zip'],
                phone=store['phoneNumber'],
                ref=store['costCenterId'],
                lon=store['longitude'],
                lat=store['latitude'],
            )
