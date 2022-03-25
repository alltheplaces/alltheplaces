# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem


class AutoZoneSpider(scrapy.Spider):

    name = "auto_zone"
    item_attributes = {"brand": "AutoZone", "brand_wikidata": "Q4826087"}
    allowed_domains = ["www.autozone.com"]
    download_delay = 0.2
    start_urls = ("https://www.autozone.com/locations/",)

    def normalize_hours(self, hours):

        all_days = []
        reversed_hours = {}

        for hour in json.loads(hours):
            all_intervals = []
            short_day = hour["day"].title()[:2]
            for interval in hour["intervals"]:
                start = str(interval["start"])
                end = str(interval["end"])
                from_hr = "{}:{}".format(
                    start[: len(start) - 2], start[len(start) - 2 :]
                )
                to_hr = "{}:{}".format(end[: len(end) - 2], end[len(end) - 2 :])
                epoch = "{}-{}".format(from_hr, to_hr)
                all_intervals.append(epoch)
            reversed_hours.setdefault(", ".join(all_intervals), [])
            reversed_hours[epoch].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == "00:00-24:00":
            return "24/7"
        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append("{} {}".format(value[0], key))
            else:
                opening_hours.append("{}-{} {}".format(value[0], value[-1], key))
        return "; ".join(opening_hours)

    def parse_location(self, response):
        opening_hours = response.xpath(
            '//span[@class="c-location-hours-today js-location-hours"]/@data-days'
        ).extract_first()
        opening_hours = self.normalize_hours(opening_hours)

        props = {
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "city": response.xpath(
                '//span[@class="c-address-city"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()'
            ).extract_first(),
            "ref": response.url,
            "website": response.url,
            "opening_hours": opening_hours,
        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):
        locations = response.xpath(
            '//a[@class="c-location-grid-item-link"]/@href'
        ).extract()

        if not locations:
            yield self.parse_location(response)
        else:
            for location in locations:
                yield scrapy.Request(
                    url=response.urljoin(location), callback=self.parse_location
                )

    def parse_state(self, response):
        for city in response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href'
        ).extract():
            yield scrapy.Request(
                url=response.urljoin(city), callback=self.parse_city_stores
            )

    def parse(self, response):
        for state in response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href'
        ).extract():
            yield scrapy.Request(url=response.urljoin(state), callback=self.parse_state)
