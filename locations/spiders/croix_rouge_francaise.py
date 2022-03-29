# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class CroixRougeFrancaiseSpider(scrapy.Spider):
    name = "croix_rouge_francaise"
    item_attributes = {"brand": "Croix-Rouge française", "brand_wikidata": "Q3003244"}
    allowed_domains = ["croix-rouge.fr"]
    start_urls = [
        "https://www.croix-rouge.fr/index_bridge.php?exportStructures=1&dpts_reg[]=&filiereTheme[]=&actionsTheme[]=&geojson",
    ]

    def parse(self, response):
        data = response.json()

        for feature in data["features"]:
            city_postal = feature["properties"]["address2"]
            postal, city = re.search(r"(\d{5})\s+(.*)", city_postal).groups()
            state = feature["properties"]["num_dept"]
            if state == "97":
                state = postal[:3]

            properties = {
                "name": feature["properties"]["name"],
                "ref": feature["id"],
                "addr_full": feature["properties"]["address1"].strip(),
                "city": city,
                "state": state,  # actually department
                "postcode": postal,
                "country": "FR",
                "phone": feature["properties"]["telephone"],
                "website": feature["properties"]["site"],
                "lat": float(feature["geometry"]["coordinates"][1]),
                "lon": float(feature["geometry"]["coordinates"][0]),
                "extras": {"type": feature["properties"]["type"]},
            }

            yield GeojsonPointItem(**properties)
