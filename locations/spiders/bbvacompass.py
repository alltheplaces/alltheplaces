# -*- coding: utf-8 -*-
import html
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BbvaCompassSpider(scrapy.Spider):
    name = "bbvacompass"
    item_attributes = {"brand": "BBVA Compass"}
    allowed_domains = ["bbvausa.com"]
    start_urls = [
        "https://www.bbvausa.com/USA",
    ]

    def parse_hours(self, hours):
        return ";".join(hours)

    def parse_location(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": html.unescape(data["name"]),
            "ref": "_".join(
                re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()
            ),
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"].get("addressCountry"),
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(data.get("openingHours", []))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath(
            '//div[contains(@class, "container-content")]//ul/li/a/@href'
        ).extract()

        if urls:
            for url in urls:
                yield scrapy.Request(response.urljoin(url))

        else:
            urls = response.xpath('//div[@class="address-block"]//a/@href').extract()
            for url in urls:
                yield scrapy.Request(
                    response.urljoin(url), callback=self.parse_location
                )
