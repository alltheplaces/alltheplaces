# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class NandosSASpider(scrapy.Spider):
    name = "nandos_sa"
    item_attributes = {"brand": "Nando's", "brand_wikidata": "Q3472954"}
    allowed_domains = ["nandos.sa"]
    start_urls = [
        "https://nandos.sa/eat/restaurants/all",
    ]
    download_delay = 0.3

    def parse(self, response):
        urls = response.xpath(
            '//li[@class="accordion-listing__item"]/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "address")]/text()'
        ).extract_first()

        if data:
            store_data = json.loads(data)
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

            properties = {
                "name": store_data["name"],
                "ref": ref,
                "addr_full": store_data["address"]["streetAddress"],
                "city": store_data["address"]["addressLocality"],
                "state": store_data["address"]["addressRegion"],
                "postcode": store_data["address"]["postalCode"],
                "phone": store_data["contactPoint"][0].get("telephone"),
                "website": response.url,
                "country": "SA",
                "lat": store_data["geo"]["latitude"],
                "lon": store_data["geo"]["longitude"],
            }

            yield GeojsonPointItem(**properties)
