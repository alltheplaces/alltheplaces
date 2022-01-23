# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class BankOfAmericaSpider(scrapy.Spider):
    name = "bankofamerica"
    item_attributes = {"brand": "Bank of America", "brand_wikidata": "Q487907"}
    download_delay = 0.1
    allowed_domains = ["bankofamerica.com"]
    start_urls = ("https://locators.bankofamerica.com/",)

    def parse(self, response):
        states = response.xpath('//ul//a[contains(@name, "State_")]/@href')
        for state in states:
            yield scrapy.Request(
                response.urljoin(state.extract()), callback=self.parse_state
            )

    def parse_state(self, response):
        cities = response.xpath('//ul//a[contains(@name, "City_")]/@href')
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city.extract()), callback=self.parse_city
            )

    def parse_city(self, response):
        centers = response.xpath(
            '//div[@class="map-list-item"]//a[contains(@name, "View_")]/@href'
        )

        for center in centers:
            yield scrapy.Request(
                response.urljoin(center.extract()), callback=self.parse_center
            )

    def parse_center(self, response):
        ref = response.url.rsplit("-", 1)[-1].split(".")[0]
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]//text()'
        ).extract():
            if "SpecialAnnouncement" in ldjson:
                # Contains broken json and is irrelevant
                continue
            yield self.parse_entity(ldjson, ref)

    def parse_entity(self, ldjson, page_ref):
        # Each feature has a BankOrCreditUnion and then either a FinancialService
        # or an AutomatedTeller. Loop over them to find a single item.
        properties = {"extras": {}}
        for ent in json.loads(ldjson):
            if "geo" not in ent:
                continue
            properties.update(
                {
                    "ref": page_ref,
                    "website": ent["url"],
                    "lat": ent["geo"]["latitude"],
                    "lon": ent["geo"]["longitude"],
                    "addr_full": ent["address"]["streetAddress"],
                    "city": ent["address"]["addressLocality"],
                    "state": ent["address"]["addressRegion"],
                    "postcode": ent["address"]["postalCode"],
                    "country": ent["address"]["addressCountry"]["name"],
                }
            )

            if ent["@type"] != "AutomatedTeller":
                # Skip over ATM customer service and the shorter name
                properties.update({"name": ent["name"], "phone": ent["telephone"]})
            if "openingHours" in ent:
                properties.update({"opening_hours": ent["openingHours"]})
            if ent["@type"] != "BankOrCreditUnion":
                # i.e. the interesting of the two types
                properties["extras"].update({"type": ent["@type"]})
        return GeojsonPointItem(**properties)
