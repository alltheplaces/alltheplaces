# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class ValeroSpider(scrapy.Spider):
    name = "valero"
    item_attributes = {"brand": "Valero", "brand_wikidata": "Q1283291"}
    allowed_domains = ["valero.com"]
    start_urls = ["https://locations.valero.com/sitemap.xml"]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        amenities = [
            s.strip()
            for s in response.xpath('//div[@class="amenityIconLabel"]/text()').extract()
        ]
        properties = {
            "lat": response.xpath(
                '//meta[@property="place:location:latitude"]/@content'
            ).get(),
            "lon": response.xpath(
                '//meta[@property="place:location:longitude"]/@content'
            ).get(),
            "ref": response.url.rsplit("/", 1)[-1],
            "website": response.url,
            "name": response.xpath(
                'normalize-space(//*[@id="pageTitleStoreName"])'
            ).get(),
            "addr_full": response.xpath(
                'normalize-space(//div[@class="locationDetailsContactRow"][1]//br/..)'
            ).get(),
            "phone": response.xpath('//a[contains(@href,"tel:")]/text()').get(),
            "opening_hours": "24/7" if "24 Hour" in amenities else None,
            "extras": {
                "atm": "ATM" in amenities,
                "amenity:fuel": True,
                "amenity:toilets": "Public Restroom" in amenities or None,
                "car_wash": "Car Wash" in amenities,
                "fuel:diesel": "Diesel" in amenities or None,
                "fuel:e85": "E-85" in amenities or None,
            },
        }
        yield GeojsonPointItem(**properties)
