# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BluePearlPetHospitalSpider(scrapy.Spider):
    name = "blue_pearl_pet_hospital"
    allowed_domains = ["bluepearlvet.com"]
    start_urls = [
        "https://bluepearlvet.com/hospital-sitemap.xml",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//url/loc/text()").extract():
            if url == "https://bluepearlvet.com/hospital/":
                pass
            elif (
                "our-vets" in url
                or "referring-vets" in url
                or "specialties-services" in url
            ):
                pass
            else:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath(
                '//*/script[@type="application/ld+json"]/text()'
            ).extract_first()
        )

        if data["address"]["addressLocality"] == "":
            pass
        else:
            properties = {
                "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
                "name": data["name"],
                "addr_full": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data["telephone"],
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
