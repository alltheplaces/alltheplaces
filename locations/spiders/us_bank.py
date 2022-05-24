# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class UsBankSpider(scrapy.Spider):
    name = "us_bank"
    download_delay = 0.5
    concurrent_requests = 3
    item_attributes = {"brand": "US Bank", "brand_wikidata": "Q739084"}
    allowed_domains = ["usbank.com"]
    start_urls = [
        "https://locations.usbank.com/index.html",
    ]

    def parse(self, response):
        state_urls = response.xpath('//*[@class="stateListItemLi"]/a/@href').extract()

        for state_url in state_urls:
            yield scrapy.Request(
                url=response.urljoin(state_url), callback=self.parse_cities
            )

    def parse_cities(self, response):
        city_urls = response.xpath('//*[@class="cityListItemLi"]/a/@href').extract()

        for city_url in city_urls:
            yield scrapy.Request(
                url=response.urljoin(city_url), callback=self.parse_stores
            )

    def parse_stores(self, response):
        store_urls = response.xpath(
            '//*[@class="btn btn-branch-default btn-top"]/@href'
        ).extract()

        for store_url in store_urls:
            yield scrapy.Request(
                url=response.urljoin(store_url), callback=self.parse_store_info
            )

    def opening_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = re.search(r".org\/(.{2})", hour["dayOfWeek"]).group(1)
            start = re.search(r"^(.*):", hour["opens"]).group(1)
            end = re.search(r"^(.*):", hour["closes"]).group(1)

            opening_hours.add_range(day=day, open_time=start, close_time=end)

        return opening_hours.as_opening_hours()

    def parse_store_info(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json"]/text()'
                ).extract_first()
            )

            properties = {
                "ref": data[0]["branchCode"],
                "name": data[0]["name"],
                "addr_full": data[0]["address"]["streetAddress"],
                "city": data[0]["address"]["addressLocality"],
                "state": data[0]["address"]["addressRegion"],
                "postcode": data[0]["address"]["postalCode"],
                "country": data[0]["address"]["addressCountry"],
                "lat": data[0]["geo"]["latitude"],
                "lon": data[0]["geo"]["longitude"],
                "website": response.url,
            }

            hours = self.opening_hours(data[0]["openingHoursSpecification"])

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
        except:
            pass
