# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_TRANSLATE = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su"
}


class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {'brand': 'Lidl', 'brand_wikidata': "Q151954"}
    allowed_domains = ["lidl.de"]
    start_urls = [
        'https://www.lidl.de/de/filialsuche/s940',
    ]
    download_delay = 0.5

    def parse(self, response):
        state_blocks = response.xpath('//div[@id="store-search-province"]/dl')
        for state_block in state_blocks:
            state = state_block.xpath('./dt/text()').extract_first()
            properties = {"state": state}
            city_urls = state_block.xpath('./dd/a/@href').extract()
            for url in city_urls:
                yield scrapy.Request(url=response.urljoin(url),
                                     meta={'properties': properties},
                                     callback=self.parse_city_stores)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day, times = re.search(r'([A-Za-z]{2})\s(.+)', hour).groups()
            if times.lower() == "closed":
                continue
            open_time, close_time = times.split('-')
            opening_hours.add_range(day=DAY_TRANSLATE[day], open_time=open_time, close_time=close_time)
        return opening_hours.as_opening_hours()

    def parse_city_stores(self, response):
        properties = response.meta["properties"]

        data = response.xpath('//script[contains(text(), "salePoints")]/text()')\
            .re_first("salePoints = eval\((\[\{.*\}\])\)")
        data = json.loads(data)

        for store in data:

            properties.update({
                'name': store["name"],
                'ref': store["ID"],
                'addr_full': store["STREET"],
                'city': store["CITY"],
                'postcode': store["ZIPCODE"],
                'country': store["COUNTRY"],
                'website': "https://www.lidl.de/" + store["url"],
                'lat': float(store["X"]),  # their X/Ys are mixed up
                'lon': float(store["Y"]),
            })

            hours = self.parse_hours(store["parsedopeningTimes"]['regular'])
            if hours:
                properties['opening_hours'] = hours

            yield GeojsonPointItem(**properties)
