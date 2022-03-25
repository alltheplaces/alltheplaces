# -*- coding: utf-8 -*-
import urllib.parse

import scrapy

from locations.items import GeojsonPointItem


class CaribouCoffeeSpider(scrapy.Spider):

    name = "caribou_coffee"
    item_attributes = {"brand": "Caribou Coffee", "brand_wikidata": "Q5039494"}
    allowed_domains = ["locations.cariboucoffee.com"]

    start_urls = ("https://locations.cariboucoffee.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            path = urllib.parse.urlparse(url).path
            if path.count("/") != 4:
                continue
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        main = response.xpath('//h1[@itemprop="name"]/..')

        ref = urllib.parse.parse_qs(
            urllib.parse.urlparse(
                response.css('script[src*="storeCode"]').attrib["src"]
            ).query
        )["storeCode"][0]

        properties = {
            "name": main.xpath('.//*[@itemprop="name"]/text()').get(),
            "lat": main.xpath('.//*[@itemprop="latitude"]/@content').get(),
            "lon": main.xpath('.//*[@itemprop="longitude"]/@content').get(),
            "ref": ref,
            "website": response.url,
            "addr_full": main.xpath('.//*[@itemprop="streetAddress"]/@content').get(),
            "city": main.xpath('.//*[@itemprop="addressLocality"]/@content').get(),
            "state": main.xpath('.//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": main.xpath('.//*[@itemprop="postalCode"]/text()').get(),
            "country": main.xpath('.//*[@itemprop="addressCountry"]/text()').get(),
            "phone": main.xpath('.//*[@itemprop="telephone"]/text()').get(),
            "opening_hours": "; ".join(
                main.xpath('.//*[@itemprop="openingHours"]/@content').extract()
            ),
        }
        yield GeojsonPointItem(**properties)
