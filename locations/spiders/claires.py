# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ClairesSpider(scrapy.Spider):
    name = "claires"
    item_attributes = {"brand": "Claire's", "brand_wikidata": "Q2974996"}
    allowed_domains = ["claires.com"]

    def start_requests(self):
        base_url = "https://stores.claires.com/us/"

        states = [
            "al",
            "ak",
            "az",
            "ar",
            "ca",
            "co",
            "ct",
            "dc",
            "de",
            "fl",
            "ga",
            "hi",
            "id",
            "il",
            "in",
            "ia",
            "ks",
            "ky",
            "la",
            "me",
            "md",
            "ma",
            "mi",
            "mn",
            "ms",
            "mo",
            "mt",
            "ne",
            "nv",
            "nh",
            "nj",
            "nm",
            "ny",
            "nc",
            "nd",
            "oh",
            "ok",
            "or",
            "pa",
            "ri",
            "sc",
            "sd",
            "tn",
            "tx",
            "ut",
            "vt",
            "va",
            "wa",
            "wv",
            "wi",
            "wy",
            "ab",
            "bc",
            "mb",
            "nb",
            "nl",
            "ns",
            "on",
            "pe",
            "pr",
            "qc",
            "sk",
            "vi",
        ]

        for state in states:
            url = base_url + state
            yield scrapy.Request(url=url, callback=self.parse_cities)

    def parse_cities(self, response):
        city_urls = response.xpath(
            '//*[@class="map-list-item is-single"]/a/@href'
        ).extract()

        for city_url in city_urls:
            yield scrapy.Request(url=city_url, callback=self.parse_stores)

    def parse_stores(self, response):
        store_urls = response.xpath(
            '//*[@class="map-list-item-header"]/a/@href'
        ).extract()

        for store_url in store_urls:
            yield scrapy.Request(url=store_url, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = hours.replace(" - ", " ")
        hours = hours.split(" ")

        if len(hours) == 22:
            for idx, val in enumerate(hours):
                if idx in (0, 3, 6, 9, 12, 15, 18):
                    day = val
                if idx in (1, 4, 7, 10, 13, 16, 19):
                    start = val
                if idx in (2, 5, 8, 11, 14, 17, 20):
                    end = val

                    opening_hours.add_range(day=day, open_time=start, close_time=end)

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "PostalAddress")]/text()'
            ).extract_first()
        )

        data = data[0]

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"].rstrip(),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "phone": data["address"]["telephone"],
            "website": response.url,
        }

        hours = self.parse_hours(data["openingHours"])

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
