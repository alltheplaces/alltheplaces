# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class AveraSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "avera"
    item_attributes = {
        "brand": "Avera",
    }
    allowed_domains = ["www.avera.org"]
    start_urls = ("https://www.avera.org",)

    def parse(self, response):
        for i in range(1, 42):
            url = "https://www.avera.org/locations/search-results/?searchId=8cae134b-aa2a-ec11-a84a-000d3a611c21&sort=13&page={}".format(
                i
            )
            yield scrapy.Request(url=url, callback=self.parse_loc)

    def parse_loc(self, response):
        locs = response.xpath('//div[@class="LocationsList"]//a/@href').extract()
        for l in locs:
            if l.startswith("../profile"):
                loc_url = l.replace("..", "https://www.avera.org/locations")
                yield scrapy.Request(
                    response.urljoin(loc_url), callback=self.parse_data
                )

    def parse_data(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "latitude")]/text()'
                ).extract_first()
            )
        except:
            data = "skip"
        if data != "skip":
            try:
                pc = data["address"]["postalCode"]
            except:
                pc = ""
            if len(data["address"]["streetAddress"].split(",")) == 2:
                properties = {
                    "ref": data["url"],
                    "name": data["name"],
                    "addr_full": data["address"]["streetAddress"].split(",")[0],
                    "housenumber": data["address"]["streetAddress"].split(",")[1],
                    "city": data["address"]["addressLocality"],
                    "state": data["address"]["addressRegion"],
                    "postcode": pc,
                    "country": "US",
                    "phone": data.get("telephone"),
                    "lat": float(data["geo"]["latitude"]),
                    "lon": float(data["geo"]["longitude"]),
                }
                yield GeojsonPointItem(**properties)
            else:
                properties = {
                    "ref": data["url"],
                    "name": data["name"],
                    "addr_full": data["address"]["streetAddress"].split(",")[0],
                    "housenumber": "",
                    "city": data["address"]["addressLocality"],
                    "state": data["address"]["addressRegion"],
                    "postcode": pc,
                    "country": "US",
                    "phone": data.get("telephone"),
                    "lat": float(data["geo"]["latitude"]),
                    "lon": float(data["geo"]["longitude"]),
                }
                yield GeojsonPointItem(**properties)
