# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class QuestDiagnosticsSpider(scrapy.Spider):
    name = "quest_diagnostics"
    item_attributes = {"brand": "Quest Diagnostics", "brand_wikidata": "Q7271456"}
    allowed_domains = ["www.questdiagnostics.com"]
    start_urls = ["https://www.questdiagnostics.com/locations-sitemap.xml"]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//url/loc/text()").extract():
            yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract():
            # Unescaped newlines
            ldjson = re.sub(r'"description": "[^"]*",', "", ldjson, flags=re.M)
            data = json.loads(ldjson)
            if data["@type"] != "LocalBusiness":
                continue

            lat = response.xpath('//div[@class="latitude"]/text()').get()
            lon = response.xpath('//div[@class="longitude"]/text()').get()

            properties = {
                "ref": data["@id"],
                "lat": lat,
                "lon": lon,
                "name": data["name"],
                "website": response.url,
                "phone": data["telephone"],
                "extras": {"fax": data["faxNumber"]},
                "addr_full": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
            }
            yield GeojsonPointItem(**properties)
