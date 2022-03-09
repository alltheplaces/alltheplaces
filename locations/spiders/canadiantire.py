# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Selector

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class CanadianTireSpider(scrapy.Spider):
    name = "canadiantire"
    allowed_domains = ["canadiantire.ca"]
    start_urls = [
        "https://www.canadiantire.ca/sitemap_0_4.xml.gz",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour, day in zip(hours, DAYS):
            if hour == "Closed":
                continue
            hour = json.loads(hour)
            opening_hours.add_range(
                day, open_time=hour["open"], close_time=hour["close"]
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        for url in urls:
            if "store-details" in url:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        check = response.xpath(
            '//tr[contains(@class, "hours-table")]/@data-working-hours'
        ).extract_first()
        if not check or check == "12:00 AM - 12:00 AM":
            # there's some empty/placeholder/test store pages
            return

        data = json.loads(
            response.xpath(
                '//div[@data-component="StoreLocatorPage"]/@data-config'
            ).extract_first()
        )

        properties = {
            "brand": "Canadian Tire",
            "name": data["storeName"],
            "ref": data["storeNumber"],
            "addr_full": data["storeAddress1"],
            "city": data["storeCityName"],
            "state": data["storeProvince"],
            "postcode": data["storePostalCode"],
            "country": "CA",
            "phone": data["storeTelephone"],
            "website": response.url,
            "lat": float(data["storeLatitude"]),
            "lon": float(data["storeLongitude"]),
        }

        hours = self.parse_hours(
            response.xpath(
                '//tr[contains(@class, "hours-table")]/@data-working-hours'
            ).extract()
        )
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
