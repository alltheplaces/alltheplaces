# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class PetValuSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "petvalu"
    item_attributes = {"brand": "Pet Valu", "brand_wikidata": "Q58009635"}
    allowed_domains = ["store.petvalu.ca"]
    start_urls = (
        "https://store.petvalu.ca/modules/multilocation/?near_location=toronto&threshold=40000000000000&geocoder_components=country:CA&distance_unit=km&limit=20000000000&services__in=&language_code=en-us&published=1&within_business=true",
    )

    def parse(self, response):
        data = response.json()
        for i in data["objects"]:
            properties = {
                "ref": i["location_url"],
                "name": i["location_name"],
                "addr_full": i["formatted_address"],
                "postcode": i["postal_code"],
                "country": i["country_name"],
                "lat": i["lat"],
                "lon": i["lon"],
            }

            yield GeojsonPointItem(**properties)
