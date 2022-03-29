# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class LuxotticaSpider(scrapy.Spider):
    name = "luxottica"
    allowed_domains = ["locations.searsoptical.com", "local.targetoptical.com"]
    start_urls = [
        "https://locations.searsoptical.com/",
        "https://local.targetoptical.com/",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for group in hours:
            if "Closed" or "All" in group:
                pass
            else:
                days, open_time, close_time = re.search(
                    r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group
                ).groups()
                days = days.split(",")
                for day in days:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath(
            '//a[@class="c-directory-list-content-item-link" or @class="c-location-grid-item-link"]/@href'
        ).extract()
        # If cannot find 'c-directory-list-content-item-link' or 'c-location-grid-item-link' then this is a store page
        if len(urls) == 0:
            properties = {
                "name": response.xpath(
                    '//div[@class="location-subheader"]/text() | //*[@class="c-location-title-geo h1-font-gray-5"]/text()'
                ).extract_first(),
                "addr_full": response.xpath(
                    '//*[@itemprop="streetAddress"]/text() | //*[@itemprop="streetAddress"]/@content'
                ).extract_first(),
                "city": response.xpath(
                    '//*[@itemprop="addressLocality"]/text() | //*[@itemprop="addressLocality"]/@content'
                ).extract_first(),
                "state": response.xpath(
                    '//*[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//*[@itemprop="postalCode"]/text()'
                ).extract_first(),
                "phone": response.xpath(
                    '//*[@itemprop="telephone"]/text()'
                ).extract_first(),
                "ref": "_".join(
                    re.search(
                        r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url
                    ).groups()
                ),
                "website": response.url,
                "lat": response.xpath(
                    '//*[@itemprop="latitude"]/@content'
                ).extract_first(),
                "lon": response.xpath(
                    '//*[@itemprop="longitude"]/@content'
                ).extract_first(),
                "brand": response.xpath(
                    '//*[@class="c-location-title"]/text() | //*[@itemprop="name"]/span/text()'
                ).extract_first(),
            }

            hours = self.parse_hours(
                response.xpath('//*[@itemprop="openingHours"]/@content').extract()
            )
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
        else:
            for path in urls:
                yield scrapy.Request(url=response.urljoin(path), callback=self.parse)
