# -*- coding: utf-8 -*-
import html
import scrapy
import re
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class ChaseSpider(scrapy.Spider):
    name = "chase"
    item_attributes = {"brand": "Chase", "brand_wikidata": "Q524629"}
    allowed_domains = ["chase.com"]
    start_urls = ("https://locator.chase.com/sitemap.xml",)

    def parse_hours(self, hours):
        o = OpeningHours()

        for h in hours:
            try:
                day, open, close = re.search(r"(.{2})\s([\d:]+)-([\d:]+)", h).groups()
                o.add_range(day, open_time=open, close_time=close, time_format="%H:%M")
            except AttributeError:
                continue

        return o.as_opening_hours()

    def parse(self, response):

        regex = re.compile(r"https://locator.chase.com/\w+/\S+(?=</loc>)")
        urls = re.findall(regex, response.text)

        for path in urls:
            path = html.unescape(path)
            if "chase.com/es/" in path:
                continue
            if re.match(r"https://locator.chase.com/.+?/.+?/.+$", path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                continue

    def parse_store(self, response):

        atm_only = True
        if response.xpath('//div[@class="Core-branch"]/*[1]').extract_first():
            atm_only = False

        name = response.xpath('//h1[@itemprop="name"]//text()').extract_first()
        if atm_only and name and " atm" not in name.lower():
            name += " ATM"

        properties = {
            "name": name.strip(),
            "ref": re.search(r"https://locator.chase.com/(.+)$", response.url).groups()[
                0
            ],
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "website": response.url,
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
        }

        hours = response.xpath('//tr[@itemprop="openingHours"]/@content').extract()[
            :7
        ]  # lobby hours only
        opening_hours = self.parse_hours(hours)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)
