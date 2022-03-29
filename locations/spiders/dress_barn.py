# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class DressBarn(scrapy.Spider):

    name = "dressbarn"
    item_attributes = {"brand": "Dress Barn"}
    download_delay = 0.2
    allowed_domains = ("locations.dressbarn.com",)
    start_urls = ("https://locations.dressbarn.com",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day, hrs = hour.split(" ")
            if hrs == "Closed":
                continue
            open_time, close_time = hrs.split("-")
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):

        props = {
            "name": response.xpath(
                '//span[@id="location-name"]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@itemprop="telephone"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//*[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//*[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "ref": response.url,
            "website": response.url,
        }

        opening_hours = self.parse_hours(
            response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        )
        if opening_hours:
            props["opening_hours"] = opening_hours

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        stores = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for url in urls:
            if url.count("/") == 2:
                callback = self.parse_stores
            elif url.count("/") == 1:
                callback = self.parse_city_stores
            else:
                callback = self.parse
            yield scrapy.Request(
                response.urljoin(url),
                callback=callback,
            )
