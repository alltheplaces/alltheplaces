# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

DAYS = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Friday": "Fr",
    "Thursday": "Th",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class VCASpider(scrapy.Spider):
    name = "vca"
    item_attributes = {"brand": "VCA"}
    allowed_domains = ["vcahospitals.com"]
    start_urls = ("https://vcahospitals.com/find-a-hospital/location-directory",)

    def parse(self, response):
        urls = response.xpath('//div[@class="hospital"]/section/h3/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        try:
            data = response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
            data = data.replace("\t", " ")
            data = json.loads(data)
        except AttributeError:
            return
        if not data:
            return

        yield GeojsonPointItem(
            lat=float(data["geo"]["latitude"]),
            lon=float(data["geo"]["longitude"]),
            phone=data["telephone"],
            website=response.url,
            ref=response.url,
            opening_hours=data["openingHours"],
            addr_full=data["address"]["streetAddress"],
            city=data["address"]["addressLocality"],
            state=data["address"]["addressRegion"],
            postcode=data["address"]["postalCode"],
            country="US",
            name=data["name"],
        )
