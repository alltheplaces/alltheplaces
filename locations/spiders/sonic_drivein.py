# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class SonicDriveinSpider(scrapy.Spider):
    name = "sonic_drivein"
    item_attributes = {"brand": "Sonic Drive-In", "brand_wikidata": "Q7561808"}
    allowed_domains = ["locations.sonicdrivein.com"]
    start_urls = [
        "https://locations.sonicdrivein.com/browse/",
    ]

    def parse(self, response):
        urls = response.xpath('//a[@class="ga-link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_state)

    def parse_state(self, response):
        urls = response.xpath('//a[@class="ga-link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_city)

    def parse_city(self, response):
        urls = set(response.xpath('//a[@class="ga-link"]/@href').extract())
        for url in urls:
            if "locations.sonicdrivein.com" not in url:
                continue
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        if data:
            data = json.loads(data)[0]
        else:
            return

        properties = {
            "ref": response.url,
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"].strip(),
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"].get("addressCountry"),
            "phone": data.get("telephone") or data["address"].get("telephone"),
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "website": data.get("url") or response.url,
        }

        hours = data.get("openingHours")
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
