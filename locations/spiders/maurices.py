# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "SUNDAY": "Su",
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
}


class MauricesSpider(scrapy.Spider):
    name = "maurices"
    item_attributes = {"brand": "Maurices", "brand_wikidata": "Q6793571"}
    allowed_domains = ["www.maurices.com", "locations.maurices.com"]
    download_delay = 0.2
    start_urls = ("https://locations.maurices.com/directory",)

    def parse_hours(self, days):
        opening_hours = OpeningHours()
        days = json.loads(days)

        for day in days:
            if not day["intervals"]:
                continue
            opening_hours.add_range(
                day=DAY_MAPPING[day["day"]],
                open_time=str(day["intervals"][0]["start"]),
                close_time=str(day["intervals"][0]["end"]),
                time_format="%H%M",
            )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):

        props = {
            "name": response.xpath(
                '//span[@class="LocationName-geo"]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@itemprop="telephone"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//*[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//*[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "country": response.xpath(
                '//*[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
            "ref": response.url,
            "website": response.url,
            "brand": response.xpath(
                '//span[@class="LocationName-brand"]/text()'
            ).extract_first(),
        }

        opening_hours = self.parse_hours(
            response.xpath(
                '//*[contains(@class, "js-hours-today")]/@data-days'
            ).extract_first()
        )
        if opening_hours:
            props["opening_hours"] = opening_hours

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        stores = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for url in urls:
            if (".." in url and url.count("/") == 4) or (
                ".." not in url and url.count("/") == 3
            ):
                callback = self.parse_stores
            elif url.count("/") == 3:
                callback = self.parse_city_stores
            else:
                callback = self.parse
            yield scrapy.Request(
                response.urljoin(url),
                callback=callback,
            )
