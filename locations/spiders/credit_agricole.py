# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class CreditAgricoleSpider(scrapy.Spider):
    name = "credit_agricole"
    item_attributes = {"brand": "Credit Agricole", "brand_wikidata": "Q590952"}
    allowed_domains = ["credit-agricole.fr"]
    start_urls = [
        "https://www.credit-agricole.fr/particulier/agence.html",
    ]

    def parse(self, response):
        urls = response.xpath('//ul[@class="indexCR-list"]/li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_provence)

    def parse_provence(self, response):
        province_urls = response.xpath(
            '//ul[@class="alphabetList js-alphabetList"]/li/a/@href'
        ).extract()

        for province in province_urls:
            yield scrapy.Request(
                response.urljoin(province), callback=self.parse_locality
            )

    def parse_locality(self, response):
        locality_urls = response.xpath(
            '//a[@class="storeLoc-selectAgency"]/@href'
        ).extract()

        for locality in locality_urls:
            yield scrapy.Request(
                response.urljoin(locality), callback=self.parse_location
            )

    def parse_location(self, response):
        ref = re.search(r".+-(.+?)/?(?:\.html|$)", response.url).group(1)
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )
            geodata = json.loads(
                response.xpath(
                    '//div[@class="CardAgencyMap js-CardAgencyMap"]/@data-value'
                ).extract_first()
            )
            properties = {
                "name": data["Name"],
                "ref": ref,
                "addr_full": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "postcode": data["address"]["postalCode"],
                "country": "FR",
                "phone": data["telephone"],
                "website": response.url,
                "lat": float(geodata["latitude"]),
                "lon": float(geodata["longitude"]),
            }

            hours = self.parse_hours(data["openingHoursSpecification"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
        except:
            pass

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["dayOfWeek"][0]
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=hour["opens"],
                close_time=hour["closes"],
                time_format="%H:%M:%S",
            )

        return opening_hours.as_opening_hours()

        properties["opening_hours"] = self.parse_hours(
            data["openingHoursSpecification"]
        )
