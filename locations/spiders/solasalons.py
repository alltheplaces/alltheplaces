# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class SolaSalonsSpider(scrapy.Spider):
    name = "solasalons"
    item_attributes = {"brand": "Sola Salons", "brand_wikidata": "Q64337426"}
    allowed_domains = ["solasalonstudios.com", "solasalonstudios.ca"]

    start_urls = [
        "https://www.solasalonstudios.com/locations",
        "https://www.solasalonstudios.ca/locations",
    ]

    def parse(self, response):
        for url in response.xpath("//@data-url").extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath('//script[@type="application/ld+json"]/text()').get()
        # unescaped control characters and double quotes
        script = re.sub(
            r'("description":).*("address":)',
            lambda m: f'{m[1]}"",{m[2]}',
            script,
            flags=re.S,
        )
        data = json.loads(script)
        properties = {
            "ref": response.url,
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "website": response.url,
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data["telephone"],
        }
        yield GeojsonPointItem(**properties)
