# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class PlanetFitnessSpider(scrapy.Spider):
    name = "planet-fitness"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    allowed_domains = [
        "planetfitness.ca",
        "planetfitness.com",
        "planetfitness.com.au",
        "planetfitness.mx",
        "planetfitness.pa",
    ]
    start_urls = ("https://www.planetfitness.com/sitemap",)
    download_delay = 4

    def parse_hours(self, response):
        hours = response.css("p.club-hours::text").get()
        if hours is not None:
            return hours.replace("\n", "; ")

    def parse(self, response):
        city_urls = response.xpath('//td[@class="club-title"]/a/@href').extract()
        for path in city_urls:
            if "/gyms/" in path:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_gym)

    def parse_gym(self, response):
        data = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )["@graph"][0]

        hours = self.parse_hours(response)

        properties = {
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "ref": response.url,
            "website": response.url,
            "phone": data["telephone"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "opening_hours": hours,
        }
        yield GeojsonPointItem(**properties)
