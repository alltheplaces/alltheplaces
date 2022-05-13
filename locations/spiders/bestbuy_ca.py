# -*- coding: utf-8 -*-
import scrapy
import json
import re
from datetime import date
from urllib.parse import urlparse, parse_qsl


from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BestBuySpider(scrapy.Spider):
    name = "bestbuy-ca"
    item_attributes = {"brand": "Best Buy", "brand_wikidata": "Q533415"}
    allowed_domains = ["stores.bestbuy.ca"]
    bb_url = "https://stores.bestbuy.ca/en-ca/index.html"

    start_urls = (bb_url,)

    def normalize_hours(self, hours):
        o = OpeningHours()

        for hour in hours:
            if hour.get("holidayHoursIsRegular") == False:
                continue

            short_day = hour["day"].title()[:2]

            for r in hour["intervals"]:
                open_time = "%04d" % r["start"]
                close_time = "%04d" % r["end"]

                o.add_range(short_day, open_time, close_time, "%H%M")

        return o.as_opening_hours()

    def parse_location(self, response):
        opening_hours = (
            response.css(".js-location-hours").xpath("@data-days").extract_first()
        )
        if opening_hours:
            opening_hours = json.loads(opening_hours)
            opening_hours = self.normalize_hours(opening_hours)

        props = {
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "city": response.xpath(
                '//span[@class="c-address-city"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
            "name": response.xpath(
                '//span[@class="LocationName-brand"]/text()'
            ).extract_first(),
            "opening_hours": opening_hours,
        }
        return GeojsonPointItem(**props)

    def parse(self, response):
        locations = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        if not locations:
            stores = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()
            if not stores:
                yield self.parse_location(response)
            for store in stores:
                yield scrapy.Request(
                    url=response.urljoin(store), callback=self.parse_location
                )
        else:
            for location in locations:
                yield scrapy.Request(
                    url=response.urljoin(location), callback=self.parse
                )
