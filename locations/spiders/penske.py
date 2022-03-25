# -*- coding: utf-8 -*-
import datetime
import re

import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Sun": "Su",
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
}


class PenskeSpider(scrapy.Spider):
    download_delay = 0.5
    name = "penske"
    item_attributes = {"brand": "Penske"}
    allowed_domains = ["pensketruckrental.com"]
    start_urls = ("https://www.pensketruckrental.com/locations",)

    def parse_hours(self, elem):
        opening_hours = OpeningHours()

        day = elem.xpath(".//dt/text()").extract()
        times = elem.xpath(".//dd/text()").extract()

        for day, times in zip(day, times):

            if times == "Closed":
                continue
            start_time, end_time = times.split(" - ")

            if start_time == "Noon":
                start_time = "12:00 PM"
            if end_time == "Noon":
                end_time = "12:00 PM"
            if "-" in day:
                days = list(DAY_MAPPING.keys())
                start_day, end_day = day.split(" - ")
                for i in days[days.index(start_day) : days.index(end_day) + 1]:
                    opening_hours.add_range(
                        day=DAY_MAPPING[i],
                        open_time=start_time,
                        close_time=end_time,
                        time_format="%I:%M %p",
                    )
            elif "," in day:
                days = list(DAY_MAPPING.keys())
                start_day, end_day = day.split(", ")
                for i in days[days.index(start_day) : days.index(end_day) + 1]:
                    opening_hours.add_range(
                        day=DAY_MAPPING[i],
                        open_time=start_time,
                        close_time=end_time,
                        time_format="%I:%M %p",
                    )
            else:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=start_time,
                    close_time=end_time,
                    time_format="%I:%M %p",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r".+/(.+)$", response.url).group(1)

        properties = {
            "addr_full": response.xpath(
                '//div[@id="location-left"]/p/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(
                response.xpath('//dt[@itemprop="latitude"]/text()').extract_first()
            ),
            "lon": float(
                response.xpath('//dt[@itemprop="longitude"]/text()').extract_first()
            ),
            "name": response.xpath('//h1[@itemprop="name"]/text()').extract_first(),
        }

        hours = self.parse_hours(response.xpath('//dl[@class="hours"]'))

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath(
            '//section[@class="locations-by-state"]/ul/li/a/@href'
        ).extract()
        if urls:
            urls.extend(
                response.xpath(
                    '//section[@class="locations-by-province"]/ul/li/a/@href'
                ).extract()
            )

        is_store = False

        if not urls:
            urls = response.xpath(
                '//section[@class="locations-by-city"]/ul/li/a/@href'
            ).extract()

        if not urls:
            urls = response.xpath(
                '//a[contains(@class,"location-link")]/@href'
            ).extract()
            is_store = True

        for url in urls:

            if is_store:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
