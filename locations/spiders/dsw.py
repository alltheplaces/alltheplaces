# -*- coding: utf-8 -*-
import re
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class DesignerShoeWarehouseSpider(scrapy.Spider):
    download_delay = 1
    name = "dsw"
    item_attributes = {"brand": "Designer Shoe Warehouse", "brand_wikidata": "Q5206207"}
    allowed_domains = [
        "stores.dsw.com",
        "stores.dsw.ca",
    ]
    start_urls = ("https://stores.dsw.com",)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="CountryList-regionList"]/div/ul/li/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)

    def parse_state(self, response):
        store = re.compile(r"^(dsw|\d+)-(\w+-?)+(\.html)?$")
        urls = (
            response.xpath('//ul[@class="StateList-listLinks"]/li/a/@href').extract()
            or response.xpath('//ul[@class="Directory-listLinks"]/li/a/@href').extract()
        )
        for path in urls:
            if store.match(path.split("/")[-1]):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city)

    def parse_city(self, response):
        store = re.compile(r"^(dsw|\d+)-(\w+-?)+(\.html)?$")
        urls = (
            response.xpath('//div[@class="CityList-content"]/ul/li/a/@href').extract()
            or response.xpath('//ul[@class="Directory-listLinks"]/li/a/@href').extract()
        )
        for path in urls:
            if store.match(path.split("/")[-1]):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse_stores(self, response):
        urls = response.xpath('//div[@id="Directory-content"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()

        phone = (
            response.xpath(
                'normalize-space(//span[@id="telephone"]/text())'
            ).extract_first()
            or response.xpath(
                'normalize-space(//div[@id="phone-main"]/text())'
            ).extract_first()
        )
        opening_hrs = (
            response.xpath('//script[@class="js-hours-config"]/text()').extract_first()
            or response.xpath(
                '//span[@class="c-location-hours-today js-location-hours"]/@data-days'
            ).extract_first()
        )
        hrs = json.loads(opening_hrs)
        if isinstance(hrs, dict):
            hrs = hrs.get("hours")

        for day in hrs:
            for interval in day.get("intervals"):
                ot = interval.get("start")
                ct = interval.get("end")
                oh.add_range(
                    day.get("day").title()[:2], str(ot), str(ct), time_format="%H%M"
                )

        properties = {
            "addr_full": response.xpath(
                '//span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "phone": phone,
            "city": response.xpath(
                '//span[@class="c-address-city"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "ref": response.xpath(
                '//span[@class="LocationName-geo"]/text()'
            ).extract_first(),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
            "opening_hours": oh.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
