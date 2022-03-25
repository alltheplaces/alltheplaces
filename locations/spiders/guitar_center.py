# -*- coding: utf-8 -*-
import datetime
import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

day_mapping = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class GuitarCenterSpider(scrapy.Spider):
    name = "guitar_center"
    item_attributes = {"brand": "Guitar Center"}
    allowed_domains = ["stores.guitarcenter.com"]
    start_urls = ("https://stores.guitarcenter.com/",)

    def parse(self, response):
        urls = response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href'
        ).extract()
        store_counts = response.xpath(
            '//span[@class="c-directory-list-content-item-count"]/text()'
        ).extract()
        store_counts = [
            int(re.search(r"(\d+)", store_count).group())
            for store_count in store_counts
        ]
        location_dir_items = dict(zip(urls, store_counts))

        is_store_list = response.xpath(
            '//a[@class="c-location-grid-item-link"][1]/@href'
        ).extract()

        if not location_dir_items and is_store_list:
            for url in is_store_list:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
        else:
            for url, store_count in location_dir_items.items():
                if store_count < 2:
                    yield scrapy.Request(
                        response.urljoin(url), callback=self.parse_store
                    )
                else:
                    yield scrapy.Request(response.urljoin(url))

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "name": response.xpath('//h1[@id="location-name"]/text()').extract_first(),
            "addr_full": response.xpath('//span[@class="c-address-street-1"]/text()')
            .extract_first()
            .strip(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()')
            .extract_first()
            .strip(),
            "country": response.xpath(
                '//abbr[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
        }

        hours = self.parse_hours(
            response.xpath(
                '//div[@class="c-location-hours-details-wrapper js-location-hours"]'
            )
        )

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, elements):

        opening_hours = OpeningHours()
        location_hours = elements.xpath(
            '//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
        ).extract_first()
        location_hours = json.loads(location_hours)

        for weekday in location_hours:
            if not weekday["intervals"]:
                continue

            open_time = str(weekday["intervals"][0]["start"])
            open_time = open_time[0:2] + ":" + open_time[2:4]

            close_time = str(weekday["intervals"][0]["end"])
            if close_time in {"0", "0000", "2400"}:
                close_time = "23:59"
            else:
                close_time = close_time[0:2] + ":" + close_time[2:4]

            opening_hours.add_range(
                day=day_mapping[weekday["day"]],
                open_time=open_time,
                close_time=close_time,
            )

        return opening_hours.as_opening_hours()
