# -*- coding: utf-8 -*-
import json
import csv
import re

import scrapy

from locations.items import GeojsonPointItem

regex = r"(?<=Imagery\/Map\/Road\/)(-?\d+\.\d+),(-?\d+\.\d+)"


class CinemarkSpider(scrapy.Spider):
    name = "cinemark"
    item_attributes = {"brand": "Cinemark"}
    allowed_domains = ["cinemark.com"]
    start_urls = ["https://www.cinemark.com/full-theatre-list"]

    def parse(self, response):
        for theatre in response.css("div.theatres-by-state li a::attr(href)").getall():
            yield scrapy.Request(response.urljoin(theatre), callback=self.parseTheatre)

    def parseTheatre(self, response):
        lat = lon = None
        geo = response.xpath(
            '//*[@id="theatreInfo"]/div[1]/div[2]/a/img/@data-src'
        ).extract_first()
        m = re.search(regex, geo)
        if m:
            lat, lon = m.group(1), m.group(2)

        data = response.xpath(
            '//body/script[@type="application/ld+json"]//text()'
        ).extract_first()
        data = json.loads(data)

        properties = {
            "lat": lat,
            "lon": lon,
            "ref": data["@id"],
            "name": data["name"],
            "addr_full": data["address"][0]["streetAddress"],
            "city": data["address"][0]["addressLocality"],
            "state": data["address"][0]["addressRegion"],
            "country": data["address"][0]["addressCountry"],
            "postcode": data["address"][0]["postalCode"],
            "phone": data.get("telephone"),
            "website": data.get("url"),
        }

        yield GeojsonPointItem(**properties)
