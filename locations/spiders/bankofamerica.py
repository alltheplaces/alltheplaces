# -*- coding: utf-8 -*-

import json
import scrapy

from locations.items import GeojsonPointItem


class BankOfAmericaSpider(scrapy.Spider):
    name = "bankofamerica"
    item_attributes = { 'brand': "Bank of America" }
    allowed_domains = ["bankofamerica.com"]
    start_urls = (
        'https://locators.bankofamerica.com/',
    )

    def parse(self, response):
        states = response.xpath('//ul//a[contains(@name, "State_")]/@href')
        for state in states:
            yield scrapy.Request(
                response.urljoin(state.extract()),
                callback=self.parse_state
            )

    def parse_state(self, response):
        cities = response.xpath('//ul//a[contains(@name, "City_")]/@href')
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city.extract()),
                callback=self.parse_city
            )

    def parse_city(self, response):
        centers = response.xpath('//div[@class="map-list-item"]//a[contains(@name, "View_")]/@href')

        for center in centers:
            yield scrapy.Request(
                response.urljoin(center.extract()),
                callback=self.parse_center
            )

    def parse_center(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').extract_first())
        opening_hours = ";".join(x["openingHours"] for x in data if x.get("openingHours"))

        yield GeojsonPointItem(
            lat=float(response.xpath('//meta[@property="og:latitude"]/@content').extract_first()),
            lon=float(response.xpath('//meta[@property="og:longitude"]/@content').extract_first()),
            phone=response.xpath('//meta[@property="og:phone_number"]/@content').extract_first(),
            website=response.url,
            ref=response.xpath('//meta[@name="twitter:title"]/@content').extract_first(),
            opening_hours=opening_hours,
            addr_full=response.xpath('//meta[@property="og:street-address"]/@content').extract_first(),
            city=response.xpath('//meta[@property="og:locality"]/@content').extract_first(),
            state=response.xpath('//meta[@property="og:region"]/@content').extract_first(),
            postcode=response.xpath('//meta[@property="og:postal-code"]/@content').extract_first(),
            country=response.xpath('//meta[@property="og:country-name"]/@content').extract_first(),
        )
