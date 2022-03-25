# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class IgaSpider(scrapy.Spider):
    name = "iga"
    item_attributes = {"brand": "IGA"}
    allowed_domains = ["iga.com"]
    start_urls = ("https://www.iga.com/consumer/locator.aspx",)

    def parse(self, response):
        next_page = response.xpath('//li[@class="next"]/a/@href').extract_first()

        stores = response.xpath('//ol[contains(@class,"results")]/li')
        for store in stores:
            position = re.search(
                r"\?daddr=(.*),(.*)",
                store.xpath(
                    './/a[contains(.,"Driving Directions")]/@href'
                ).extract_first(),
            )

            phone = store.xpath(
                './/span[contains(@class,"tel")]/text()'
            ).extract_first()
            if phone:
                phone = phone.replace("- Main", "").strip()

            yield GeojsonPointItem(
                lat=float(position[1]),
                lon=float(position[2]),
                phone=phone,
                website=store.xpath(
                    './/a[contains(.,"View Our Website")]/@href'
                ).extract_first(),
                ref=store.xpath(
                    './/div[contains(@class,"org")]/text()'
                ).extract_first(),
                addr_full=store.xpath(
                    './/div[contains(@class,"street-address")]/text()'
                ).extract_first(),
                city=store.xpath('.//span[contains(@class,"locality")]/text()')
                .extract_first()
                .rstrip(","),
                state=store.xpath('.//span[contains(@class,"region")]/text()')
                .extract_first()
                .strip(),
                postcode=store.xpath('.//span[contains(@class,"postal-code")]/text()')
                .extract_first()
                .strip(),
                country="USA",
            )

        if next_page:
            yield scrapy.Request(response.urljoin(next_page))
