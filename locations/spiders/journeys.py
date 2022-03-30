# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class JourneysSpider(scrapy.Spider):
    name = "journeys"
    item_attributes = {"brand": "Journeys"}
    allowed_domains = ["journeys.com"]
    start_urls = [
        "https://www.journeys.com/stores",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                day, open_time, close_time = re.search(
                    r"([A-Za-z]{2})\s([\d:]+)-([\d:]+)", hour
                ).groups()
            except:
                continue
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        name = response.xpath('//h2[@itemprop="name"]/text()').extract_first()

        try:
            brand, number = re.search(r"(.*?)\s#(\d+)", name).groups()
        except AttributeError:
            brand = name
            number = None

        name = response.xpath(
            'normalize-space(//p[@itemprop="streetAddress"]//text())'
        ).extract_first()  # usually the venue name
        address = response.xpath(
            'normalize-space(//div[@itemprop="address"]//p[2]/text())'
        ).extract_first()
        if not address:
            address = name  # 4 stores don't have a venue name as first line of address
            name = None

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": name,
            "addr_full": address,
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]//text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "country": response.xpath(
                'normalize-space(//*[@itemprop="addressCountry"]//text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]//text())'
            ).extract_first(),
            "website": response.url,
            "brand": brand,
            "extras": {"number": number},
        }

        hours = self.parse_hours(
            response.xpath('//*[@itemprop="openingHours"]/@datetime').extract()
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_store_list(self, response):
        urls = response.xpath('//div[@class="store-heading"]//a[1]/@href').extract()
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_store)

    def parse(self, response):
        states = response.xpath(
            '//select[@name="StateOrProvince"]/option/@value'
        ).extract()
        for state in states:
            if state:
                form_data = {
                    "StateOrProvince": state,
                    "PostalCode": "",
                    "MileRadius": "25",  # not used when search by state
                    "Latitude": "",
                    "Longitude": "",
                    "Mode": "search",
                }

                yield scrapy.http.FormRequest(
                    url="https://www.journeys.com/stores",
                    method="POST",
                    formdata=form_data,
                    # headers=HEADERS,
                    callback=self.parse_store_list,
                )
