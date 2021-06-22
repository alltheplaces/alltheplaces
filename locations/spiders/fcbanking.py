# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class FcBankingSpider(scrapy.Spider):
    name = "fcbanking"
    item_attributes = {"brand": "First Commonwealth Bank", "brand_wikidata": "Q5452773"}
    allowed_domains = ["www.fcbanking.com"]
    start_urls = [
        "https://www.fcbanking.com/sitemap/branch-locations_0.xml",
        "https://www.fcbanking.com/sitemap/branch-locations_1.xml",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc/text()").extract()

        for url in urls:
            if url == "https://www.fcbanking.com/branch-locations/":
                continue
            yield scrapy.Request(url, callback=self.parse_branch)

    def parse_branch(self, response):
        map_script = response.xpath('//script/text()[contains(., "setLat")]').get()
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()').get()
        data = json.loads(re.sub(r"^//.*$", "", ldjson, flags=re.M))

        lat = re.search(r'setLat\("(.*)"\)', map_script)[1]
        lon = re.search(r'setLon\("(.*)"\)', map_script)[1]
        address = data["address"]

        properties = {
            "lat": lat,
            "lon": lon,
            "ref": response.url,
            "name": data["name"],
            "addr_full": address["streetAddress"],
            "city": address["addressLocality"],
            "state": address["addressRegion"],
            "postcode": address["postalCode"],
            "phone": data["telephone"],
            "website": response.url,
            "opening_hours": ",".join(data["openingHours"]),
        }

        return GeojsonPointItem(**properties)
