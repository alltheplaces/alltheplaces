# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ExtendedStayAmericaSpider(scrapy.Spider):
    name = "extended_stay_america"
    item_attributes = {"brand": "Extended Stay America"}
    allowed_domains = ["extendedstayamerica.com"]
    start_urls = [
        "https://www.extendedstayamerica.com/hotels",
    ]

    def parse(self, response):
        urls = response.xpath("//tr/td/a/@href").extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="links"]//td/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel_list)

    def parse_hotel_list(self, response):
        script = response.xpath(
            '//script[contains(text(), "pinList")]/text()'
        ).extract_first()
        hotels = json.loads(re.search(r"var pinList =\s(\{.*\});", script).groups()[0])

        for hotel in hotels["PushPins"]:
            properties = {
                "name": hotel["HotelName"],
                "ref": hotel["HotelId"],
                "addr_full": hotel["Address"],
                "city": hotel["HotelCity"],
                "state": hotel["HotelState"],
                "postcode": hotel["HotelZip"],
                "country": "US",
                "website": hotel["MinisiteUrl"],
                "lat": float(hotel["Latitude"]),
                "lon": float(hotel["Longitude"]),
            }

            yield GeojsonPointItem(**properties)
