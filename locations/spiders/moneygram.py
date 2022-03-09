# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MichaelsSpider(scrapy.Spider):
    download_delay = 0.2
    name = "moneygram"
    item_attributes = {"brand": "Moneygram", "brand_wikidata": "Q1944412"}
    allowed_domains = ["locations.moneygram.com"]
    start_urls = ("http://locations.moneygram.com/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="statelist_item"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        location_urls = response.xpath(
            '//div[@class="citylist_item"]/a/@href'
        ).extract()

        for url in location_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        city_urls = response.xpath('//div[@class="addresslist_item"]/a/@href').extract()

        for url in city_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"][2]/text()'
            ).extract_first()
        )

        properties = {
            "ref": data.get("@id"),
            "addr_full": data.get("address", {}).get("streetAddress"),
            "city": data.get("address", {}).get("addressLocality"),
            "state": data.get("address", {}).get("addressRegion"),
            "postcode": data.get("address", {}).get("postalCode"),
            "postcode": data.get("name"),
            "phone": data.get("telephone"),
            "country": data.get("address", {}).get("addressCountry"),
            "lat": data.get("geo", {}).get("latitude"),
            "lon": data.get("geo", {}).get("longitude"),
            "website": data.get("url"),
            "extras": {
                "is_in": data.get("containedIn"),
            },
        }

        hours = self.parse_hours(data.get("openingHoursSpecification"))

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()
        weekdays = response

        for weekday in weekdays:
            for dow in weekday.get("dayOfWeek", []):
                opening_hours.add_range(
                    dow[:2],
                    open_time=weekday.get("opens"),
                    close_time=weekday.get("closes"),
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()
