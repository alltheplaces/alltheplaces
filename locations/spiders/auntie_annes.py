# -*- coding: utf-8 -*-
import urllib.parse

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class AuntieAnnesSpider(scrapy.Spider):
    name = "auntie_annes"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    allowed_domains = ["auntieannes.com"]
    start_urls = ("https://locations.auntieannes.com/",)

    def parse(self, response):
        for href in response.xpath(
            '(//a[@data-ya-track="todirectory"]|//a[@data-ya-track="businessname"])/@href'
        ).extract():
            url = response.urljoin(href)
            path = urllib.parse.urlparse(url).path
            if path.count("/") == 3:
                yield scrapy.Request(response.urljoin(href), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(href))

    def parse_store(self, response):
        opening_hours = OpeningHours()
        for row in response.xpath('//*[@itemprop="openingHours"]/@content').extract():
            day, hours = row.split(" ")
            if hours == "Closed":
                continue
            open_time, close_time = hours.split("-")
            opening_hours.add_range(day, open_time, close_time)

        properties = {
            "ref": urllib.parse.urlparse(
                response.xpath("//main").attrib["itemid"]
            ).fragment,
            "name": response.xpath('//meta[@property="og:title"]/@content')
            .extract_first()
            .split(" | ")[0],
            "website": response.url,
            "lat": response.xpath(
                '//meta[@itemprop="latitude"]/@content'
            ).extract_first(),
            "lon": response.xpath(
                '//meta[@itemprop="longitude"]/@content'
            ).extract_first(),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
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
            "country": response.xpath(
                '//*[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//*[@itemprop="telephone"]/text()'
            ).extract_first(),
        }
        yield GeojsonPointItem(**properties)
