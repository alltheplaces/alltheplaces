# -*- coding: utf-8 -*-
import scrapy
import json
import re

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

from locations.items import GeojsonPointItem


class DaveAndBustersSpider(scrapy.Spider):
    name = "dave_and_busters"
    item_attributes = {"brand": "Dave and Busters"}
    allowed_domains = ["daveandbusters.com"]
    start_urls = ("https://www.daveandbusters.com/locations",)

    def store_hours(self, store_hours):
        res = ""
        for day in store_hours:
            match = re.search(
                r"(\w*)(\s*-\s*(\w*))?\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)?\s*-\s*(\d{1,2})(:(\d{1,2}))?\s*(am|pm|mp)",
                day.replace("Midnight", "12:00pm"),
            )

            if not match:
                continue
            res += match[1][:2]

            try:
                res += match[2].replace(" ", "")[:3] + " "
            except Exception:
                res += " "

            if match[5]:
                first_minutes = match[5]
            else:
                first_minutes = ":00"

            if match[9]:
                second_minutes = match[9]
            else:
                second_minutes = ":00"

            res += (
                str(int(match[4]) + (12 if match[7] in ["pm", "mp"] else 0))
                + first_minutes
                + "-"
            )
            res += (
                str(int(match[8]) + (12 if match[10] in ["pm", "mp"] else 0))
                + second_minutes
                + ";"
            )

        return res.rstrip(";").strip()

    def parse(self, response):
        cities = response.xpath('//div[@class="location-list-item"]//li/a/@href')
        for place in cities:
            yield scrapy.Request(
                response.urljoin(place.extract()), callback=self.parse_shop
            )

    def parse_shop(self, response):

        times = self.store_hours(
            response.xpath('//div[contains(@class,"schedule")]/p/text()').extract()
        )
        address = re.search(
            r"(.*),\s*(\D{2})\s*(\d{5})",
            response.xpath(
                '//div[contains(@class,"location")]/p[3]/text()'
            ).extract_first(),
        )

        props = {
            "opening_hours": times,
            "phone": response.xpath(
                '//a[contains(@class,"dnb-local-info-phone")]/@href'
            )
            .extract_first()
            .replace("tel:", ""),
            "website": response.url,
            "ref": response.xpath(
                '//div[contains(@class,"location")]/p[1]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//div[contains(@class,"location")]/p[2]/text()'
            ).extract_first(),
        }

        try:
            props["postcode"] = address[3]
        except Exception as e:
            postcode = ""

        try:
            props["city"] = address[1]
        except Exception as e:
            city = ""

        try:
            props["state"] = address[2]
        except Exception as e:
            state = ""

        try:
            pos = json.loads(
                response.xpath(
                    '//head/script[@type="application/ld+json"]/text()'
                ).extract_first()
            )["geo"]
            props["lat"] = float(pos["latitude"])
            props["lon"] = float(pos["longitude"])
        except Exception as e:
            pos = ""

        yield GeojsonPointItem(**props)
