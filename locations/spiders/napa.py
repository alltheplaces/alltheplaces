# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import Feature


class NapaSpider(scrapy.Spider):
    name = "napa"
    item_attributes = {"brand": "Napa Auto Parts", "brand_wikidata": "Q6970842"}
    allowed_domains = ["napaonline.com"]
    start_urls = [
        "https://www.napaonline.com/en/auto-parts-stores-near-me",
    ]

    def parse(self, response):
        urls = response.xpath('//div[@class="box box-xpad-both nol-content-outer"]//a/@href').extract()
        for url in urls:
            if url not in ("/en/"):
                yield scrapy.Request(response.urljoin(url), callback=self.parse2ndlevel)

    def parse2ndlevel(self, response):
        urls = response.xpath('//div[@class="store-browse-content"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse3rdlevel)

    def parse3rdlevel(self, response):
        if response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first():
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )

            try:
                state = data["address"]["addressRegion"]
            except:
                state = ""

            properties = {
                "ref": data["url"],
                "name": data["name"],
                "street_address": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": state,
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data.get("telephone"),
                "lat": data["geo"]["latitude"],
                "lon": data["geo"]["longitude"],
            }

            yield Feature(**properties)
        else:
            urls = response.xpath('//div[@class="store-browse-content-listing"]//a/@href').extract()
            for url in urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse4thlevel)

    def parse4thlevel(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        try:
            state = data["address"]["addressRegion"]
        except:
            state = ""

        properties = {
            "ref": data["url"],
            "name": data["name"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": state,
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
        }

        yield Feature(**properties)
