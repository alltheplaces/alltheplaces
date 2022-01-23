# -*- coding: utf-8 -*-
import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BanfieldPetHospitalScraper(scrapy.Spider):
    name = "banfield_pet_hospital"
    item_attributes = {"brand": "Banfield Pet Hospital", "brand_wikidata": "Q2882416"}
    allowed_domains = ["www.banfield.com"]
    download_delay = 0.5
    start_urls = ("https://www.banfield.com/locations/hospitals-by-state",)

    def parse(self, response):
        for href in response.xpath(
            '//div[@class="state-hospital-name"]//@href'
        ).extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_store)

    def parse_store(self, response):
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract():
            data = json.loads(ldjson)
            if data["@type"] != ["VeterinaryCare", "LocalBusiness"]:
                continue
            ref = response.url.rsplit("/", 1)[-1]
            opening_hours = OpeningHours()
            for spec in data["openingHoursSpecification"]:
                opening_hours.add_range(
                    spec["dayOfWeek"][:2], spec["opens"], spec["closes"]
                )
            properties = {
                "ref": ref,
                "website": response.url,
                "lat": data["geo"]["latitude"],
                "lon": data["geo"]["longitude"],
                "name": data["name"],
                "addr_full": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data["telephone"],
            }
            yield GeojsonPointItem(**properties)
