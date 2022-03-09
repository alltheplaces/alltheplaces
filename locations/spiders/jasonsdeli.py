# -*- coding: utf-8 -*-
import datetime
import re

import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class JasonsDeliSpider(scrapy.Spider):
    download_delay = 0.2
    name = "jasonsdeli"
    item_attributes = {"brand": "Jason's Deli", "brand_wikidata": "Q16997641"}
    allowed_domains = ["jasonsdeli.com"]
    start_urls = ("https://www.jasonsdeli.com/restaurants",)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for item in elements:
            day, open_time, close_time = re.search(
                r"([a-z]{3}):.([0-9:\sAPM]+)\s-\s([0-9:\sAPM]+)",
                item,
                flags=re.IGNORECASE,
            ).groups()
            opening_hours.add_range(
                day=day[0:2],
                open_time=datetime.datetime.strptime(open_time, "%I:%M %p").strftime(
                    "%H:%M"
                ),
                close_time=datetime.datetime.strptime(close_time, "%I:%M %p").strftime(
                    "%H:%M"
                ),
            )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "addr_full": response.xpath('//div[@class="address"]/text()')
            .extract_first()[0]
            .split("\n")[0],
            "city": response.xpath('//div[@class="address"]/text()')
            .extract()[-1]
            .split(",")[0],
            "state": response.xpath('//div[@class="address"]/text()')
            .extract()[-1]
            .split(", ")[1]
            .split(" ")[-2],
            "postcode": response.xpath('//div[@class="address"]/text()')
            .extract()[-1]
            .split(", ")[1]
            .split(" ")[-1],
            "ref": ref,
            "website": response.url,
            "phone": response.xpath('//a[@class="cnphone"]/text()').extract_first(),
        }

        hours = self.parse_hours(
            response.xpath('//div[@class="loc-hours"]/p/text()').extract()
        )

        try:
            bus_name = (
                response.xpath('//div[@class="loc-title"]/text()')
                .extract()[0]
                .split(": ")[1]
            )
        except IndexError:
            bus_name = response.xpath(
                '//div[@class="loc-title"]/text()'
            ).extract_first()
        properties["name"] = bus_name

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//span[@class="field-content"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
