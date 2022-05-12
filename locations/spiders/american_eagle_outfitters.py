# -*- coding: utf-8 -*-
import re
import csv

import scrapy

from scrapy.selector import Selector

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AmericanEagleOutfittersSpider(scrapy.Spider):
    name = "american_eagle_outfitters"
    item_attributes = {
        "brand": "American Eagle Outfitters",
        "brand_wikidata": "Q2842931",
    }
    allowed_domains = ["ae.com"]
    start_urls = ["http://stores.aeostores.com/sitemap.xml"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                day, open_time, close_time = re.search(
                    r"([A-Za-z]{2})\s([\d:]+)-([\d:]+)", hour
                ).groups()
            except:
                continue
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        single_location = response.xpath('//*[@class="Core-address"]').extract_first()

        if single_location:

            properties = {
                "ref": "_".join(
                    re.search(
                        r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url
                    ).groups()
                ),
                "name": response.xpath(
                    '//*[@class="LocationName-geo"]/text()'
                ).extract_first(),
                "addr_full": response.xpath(
                    '//*[@class="c-address-street-1"]/text()'
                ).extract_first(),
                "city": response.xpath(
                    '//*[@class="c-address-city"]/text()'
                ).extract_first(),
                "state": response.xpath(
                    '//*[@class="c-address-state"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//*[@class="c-address-postal-code"]/text()'
                ).extract_first(),
                "country": response.xpath(
                    '//*[@itemprop="addressCountry"]/text()'
                ).extract_first(),
                "lat": response.xpath(
                    '//*[@itemprop="latitude"]/@content'
                ).extract_first(),
                "lon": response.xpath(
                    '//*[@itemprop="longitude"]/@content'
                ).extract_first(),
                "phone": response.xpath(
                    '//*[@data-ya-track="phone"]/text()'
                ).extract_first(),
                "brand": response.xpath(
                    '//*[@class="LocationName-brand"]/text()'
                ).extract_first(),
                "website": response.url,
            }

            hours = self.parse_hours(
                response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
            )

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)

        else:
            pass
