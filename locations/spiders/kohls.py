# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class KohlsSpider(scrapy.Spider):

    name = "kohls"
    item_attributes = {"brand": "Kohl's", "brand_wikidata": "Q967265"}
    download_delay = 1.5
    allowed_domains = ["www.kohls.com"]
    start_urls = ("https://www.kohls.com/stores.shtml",)

    def parse_stores(self, response):
        opening_hours = re.findall(
            r'"openingHours": "([.||\t|\n|A-Z|a-z|\-|0-9|:|\s]+)', response.text
        )
        hours = ""
        if opening_hours:
            for osm in opening_hours:
                hours = osm.split("\n")
                hours = "; ".join(
                    [
                        hour.replace(":", "").replace(" - ", "-")
                        for hour in hours
                        if hour
                    ]
                )

        properties = {
            "addr_full": response.xpath(
                '//div[@id="mainAddrLine1"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@class="indy-big-map-phone"]/text()'
            ).extract_first(),
            "city": response.xpath('//meta[@name="city"]/@content').extract_first(),
            "state": response.xpath('//meta[@name="state"]/@content').extract_first(),
            "postcode": response.xpath('//meta[@name="zip"]/@content').extract_first(),
            "name": response.xpath(
                '//div[@class="location-header"]/text()'
            ).extract_first(),
            "website": response.url,
            "lat": float(
                re.findall(r'"latitude": "([-\d]+\.[\d]+)"', response.text)[0]
            ),
            "lon": float(
                re.findall(r'"longitude": "([-\d]+\.[\d]+)"', response.text)[0]
            ),
            "ref": response.url,
            "opening_hours": hours,
        }

        return GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//span[@class="location-title"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//a[@class="citylist"]/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_city_stores
            )

    def parse(self, response):
        urls = response.xpath('//a[@class="regionlist"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
