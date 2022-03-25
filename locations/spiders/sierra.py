# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SierraSpider(scrapy.Spider):
    name = "sierra"
    item_attributes = {"brand": "Sierra"}
    allowed_domains = ["sierra.com"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.sierra.com/lp2/retail-stores/", headers=self.headers
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                opening_hours.add_range(
                    day=hour["dayOfWeek"].replace("http://schema.org/", "")[:2],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                    time_format="%H:%M:%S",
                )
            except:
                continue  # closed or no time range given

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        properties = {
            "name": data["name"],
            "ref": data["branchCode"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(data["openingHoursSpecification"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//li[contains(@class, "item")]//h4/a/@href').extract()
        for url in urls:
            yield scrapy.Request(
                response.urljoin(url), headers=self.headers, callback=self.parse_store
            )
