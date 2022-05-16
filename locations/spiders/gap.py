# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class GapSpider(scrapy.Spider):
    name = "gap"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q420822"}
    allowed_domains = ["www.gap.com"]
    start_urls = ["https://www.gap.com/stores"]

    def parse(self, response):
        for href in response.css(".map-list ::attr(href)").extract():
            if href.startswith("tel:"):
                continue
            yield scrapy.Request(response.urljoin(href))

        ldjson = response.xpath('//script[@type="application/ld+json"]/text()').get()
        data = json.loads(ldjson)[0]
        if "geo" in data:
            yield from self.parse_store(response, data)

    def parse_store(self, response, data):
        properties = {
            "ref": response.url,
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": response.xpath(
                'normalize-space(//div[@class="location-name"]/text())'
            ).get(),
            "brand": response.xpath(
                'normalize-space(//div[@class="store-carries"]/text())'
            ).get(),
            "website": response.xpath('//link[@rel="canonical"]/@href').get(),
            "opening_hours": data["openingHours"],
            "phone": data["address"]["telephone"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
        }
        yield GeojsonPointItem(**properties)
