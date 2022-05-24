# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class VerveCoffeeRoastersSpider(scrapy.Spider):
    name = "verve_coffee_roasters"
    item_attributes = {"brand": "Verve Coffee Roasters"}
    allowed_domains = ["www.vervecoffee.com"]
    start_urls = [
        "https://www.vervecoffee.com/pages/locations-all",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        days, store_hours = hours.split()
        open_time, close_time = store_hours.split("-")
        for day in days.split(","):
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.xpath(
            '//section[@itemtype="http://schema.org/CafeOrCoffeeShop"]'
        )

        for store in stores:
            properties = {
                "ref": store.xpath('.//div[@class="info text-align--center"]/a/text()')
                .extract_first()
                .strip(),
                "name": store.xpath('.//div[@class="info text-align--center"]/a/text()')
                .extract_first()
                .strip(),
                "addr_full": store.xpath(
                    'normalize-space(.//span[@itemprop="streetAddress"]//text())'
                ).extract_first(),
                "city": store.xpath(
                    'normalize-space(.//span[@itemprop="addressLocality"]//text())'
                ).extract_first(),
                "state": store.xpath(
                    'normalize-space(.//span[@itemprop="addressRegion"]//text())'
                ).extract_first(),
                "postcode": store.xpath(
                    'normalize-space(.//span[@itemprop="postalCode"]//text())'
                ).extract_first(),
                "phone": store.xpath(
                    'normalize-space(.//a[@itemprop="telephone"]//text())'
                ).extract_first(),
            }

            hours = store.xpath(
                './/meta[@itemprop="openingHours"]/@content'
            ).extract_first()
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)
