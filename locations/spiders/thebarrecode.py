# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class TheBarreCodeSpider(scrapy.Spider):
    name = "thebarrecode"
    item_attributes = {"brand": "The Barre Code"}
    allowed_domains = ["thebarrecode.com"]
    start_urls = ("http://www.thebarrecode.com/",)

    def parse(self, response):
        for location_url in response.xpath(
            '//h4[@class="studio-location-name"]/a[1]/@href'
        ).extract():
            yield scrapy.Request(
                location_url,
                callback=self.parse_location,
            )

    def parse_location(self, response):
        properties = {
            "addr_full": response.xpath(
                '//h4[@class="studio-address"]/span[@class="street"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//h4[@class="studio-address"]/span[@class="city"]/text()'
            )
            .extract_first()
            .replace(", ", ""),
            "state": response.xpath(
                '//h4[@class="studio-address"]/span[@class="state"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//h4[@class="studio-address"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//h4[@class="studio-phone"]/text()'
            ).extract_first(),
            "name": response.xpath(
                '//h3[@class="studio-location-name"]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
        }

        for key in properties:
            if properties[key] and isinstance(properties[key], str):
                properties[key] = properties[key].strip()

        lat = response.xpath('//div[@class="marker"]/@data-lat').extract_first()
        if lat:
            lat = float(lat)
            properties["lat"] = lat
        lon = response.xpath('//div[@class="marker"]/@data-lng').extract_first()
        if lon:
            lon = float(lon)
            properties["lon"] = lon

        yield GeojsonPointItem(**properties)
