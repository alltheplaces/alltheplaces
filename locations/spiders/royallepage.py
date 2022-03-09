# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class RoyalLePageSpider(scrapy.Spider):
    name = "royallepage"
    allowed_domains = ["royallepage.ca"]
    start_urls = [
        "https://www.royallepage.ca/en/search/offices/?lat=&lng=&address=&designations=&address_type=&city_name=&prov_code=&sortby=&transactionType=OFFICE&name=&location=&language=&specialization=All",
    ]

    def parse_location(self, response):
        map_url = response.xpath(
            '//div[contains(@class, "map-container")]/a/@href'
        ).extract_first()

        lat_lon = re.search(r"maps\?q=([\d\.\-]+),([\d\.\-]+)", map_url)
        if lat_lon:
            lat, lon = lat_lon.groups()
        else:
            lat, lon = None, None

        properties = {
            "brand": "Royal LePage",
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())')
            .extract_first()
            .strip(" *"),
            "addr_full": response.xpath(
                'normalize-space(//*[@itemprop="address"]/p/text())'
            ).extract_first(),
            "country": "CA",
            "phone": response.xpath(
                'normalize-space(//a[@itemprop="telephone"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath("//address//a/@href").extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

        next_page = response.xpath(
            '//div[contains(@class, "paginator")]//li[@class="is-active"]/following-sibling::li//a/@href'
        ).extract_first()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page))
