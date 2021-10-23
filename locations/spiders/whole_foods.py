# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
import json


class WholeFoodsSpider(scrapy.Spider):
    name = "whole_foods"
    item_attributes = { 'brand': "Whole Foods" }
    allowed_domains = ["www.wholefoodsmarket.com"]
    start_urls = (
        'https://www.wholefoodsmarket.com/sitemap/sitemap-stores.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        regex = re.compile(r'https://www.wholefoodsmarket.com/stores/\S+')
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):
        store_json = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        )
        yield GeojsonPointItem(
            ref=response.url.split('/')[-1],
            name=response.xpath('//h1/text()').extract_first().strip(),
            lat=float(store_json['geo']['latitude']),
            lon=float(store_json['geo']['longitude']),
            addr_full=store_json['address']['streetAddress'],
            city=store_json['address']['addressLocality'],
            state=store_json['address']['addressRegion'],
            postcode=store_json['address']['postalCode'],
            phone=store_json['telephone'],
            website=response.url,
            opening_hours=self.parse_hours(store_json['openingHoursSpecification'])
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            opening_hours.add_range(
                day=hour["dayOfWeek"].split('/')[-1][0:2],
                open_time=hour["opens"],
                close_time=hour["closes"]
            )

        return opening_hours.as_opening_hours()
