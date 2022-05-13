# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class Crunch_fitnessSpider(scrapy.Spider):
    name = "crunch_fitness"
    item_attributes = {"brand": "Crunch Fitness", "brand_wikidata": "Q5190093"}
    allowed_domains = ["crunch.com"]
    start_urls = [
        "https://www.crunch.com/locations",
    ]

    def parse(self, response):
        data = json.loads(
            response.xpath("//div[@data-react-props]/@data-react-props").extract_first()
        )

        for club in data["clubs"]:
            properties = {
                "name": club["name"],
                "ref": club["id"],
                "addr_full": club["address"]["address_1"],
                "city": club["address"]["city"],
                "state": club["address"]["state"],
                "postcode": club["address"]["zip"],
                "country": club["address"]["country_code"],
                "phone": club.get("phone"),
                "website": "https://www.crunch.com/locations/" + club["slug"],
                "lat": float(club["latitude"]),
                "lon": float(club["longitude"]),
            }

            yield GeojsonPointItem(**properties)
