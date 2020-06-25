# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su"
}


class AuchanSpider(scrapy.Spider):
    name = "auchan"
    item_attributes = {'brand': 'Auchan', 'brand_wikidata': 'Q758603'}
    allowed_domains = ['auchan.fr', "woosmap.com"]
    start_urls = [
        'https://www.auchan.fr/magasins/votremagasin?store_id=152',
    ]

    def parse(self, response):
        yield scrapy.Request('https://api.woosmap.com/stores/?key=auchan-woos&page=1', callback=self.parse_api)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day, times in hours.items():
            if day == "default":
                continue
            opening_hours.add_range(day=DAYS[day],
                                    open_time=times[0]["start"],
                                    close_time=times[-1]["end"]
                                    )

        return opening_hours.as_opening_hours()

    def parse_api(self, response):
        data = json.loads(response.body_as_unicode())

        stores = data['features']

        for store in stores:
            properties = {
                'name': store["properties"]["name"],
                'ref': store["properties"]["store_id"],
                'addr_full': " ".join(store["properties"]["address"]["lines"]),
                'city': store["properties"]["address"]["city"],
                'postcode': store["properties"]["address"]["zipcode"],
                'country': store["properties"]["address"]["country_code"],
                'phone': store["properties"]["contact"]["phone"],
                'website': store["properties"]["contact"]["website"],
                'lat': float(store["geometry"]["coordinates"][1]),
                'lon': float(store["geometry"]["coordinates"][0]),
            }

            hours = self.parse_hours(store["properties"]["opening_hours"]["usual"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)

        if data['pagination']['page'] < data['pagination']['pageCount']:
            page = data['pagination']['page'] + 1
            yield scrapy.Request(
                url='https://api.woosmap.com/stores/?key=auchan-woos&page={page}'.format(page=page),
                callback=self.parse_api
            )
