# -*- coding: utf-8 -*-
import scrapy
import json
import traceback
import re
from locations.items import GeojsonPointItem


class TacobellSpider(scrapy.Spider):
    name = "tacobell"
    item_attributes = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}
    allowed_domains = ["locations.tacobell.com"]
    start_urls = ("https://locations.tacobell.com/",)
    download_delay = 0.2

    def normalize_hours(self, hours):

        all_days = []
        reversed_hours = {}

        for hour in json.loads(hours):
            all_intervals = []
            short_day = hour["day"].title()[:2]

            if not hour["intervals"]:
                continue

            for interval in hour["intervals"]:
                start = str(interval["start"]).zfill(4)
                end = str(interval["end"]).zfill(4)
                from_hr = "{}:{}".format(start[:2], start[2:])
                to_hr = "{}:{}".format(end[:2], end[2:])
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
        if not response.xpath('//div[@itemprop="department"]'):
            return

        hours = response.xpath(
            '//div[@class="c-hours-details-wrapper js-hours-table"]/@data-days'
        ).extract_first()
        opening_hours = hours and self.normalize_hours(hours)

        props = {
            "addr_full": response.xpath('//meta[@itemprop="streetAddress"]/@content')
            .extract_first()
            .strip(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@itemprop="telephone"]/text()'
            ).extract_first(),
            "ref": response.xpath(
                '//div[@itemprop="department"]/@data-code'
            ).extract_first(),
            "website": response.url,
            "opening_hours": opening_hours,
        }

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):
        yield self.parse_location(response)
        locations = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()

        for location in locations:
            yield scrapy.Request(
                url=response.urljoin(location), callback=self.parse_location
            )

    def parse_state(self, response):
        cities = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city), callback=self.parse_city_stores
            )

    def parse(self, response):
        states = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        # The web site currently special-cases DC by linking directly to the
        # page for the one store therein, bypassing the state index page.
        # (This spider will call parse_state on the store page and fail.)
        # Un-special case this by inserting a link to the state index page
        # which does in fact exist. Hopefully this is bulletproof if the
        # web site changes.
        states.append("dc.html")

        for state in states:
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)
