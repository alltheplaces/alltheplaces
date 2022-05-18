# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class McLocalizer(scrapy.Spider):

    name = "mclocalizer"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = [
        "www.mcdonalds.com",
        "www.mcdonalds.com.pr",
        "www.mcdonalds.co.cr",
        "www.mcdonalds.com.ar",
        "www.mcdonalds.com.pa",
        "www.mcdonalds.com.br",
        "www.mcdonalds.com.ve",
        "www.mcdonalds.com.mx",
        "www.mcdonalds.cl",
        "www.mcdonalds.com.uy",
        "www.mcdonalds.com.co",
    ]

    start_urls = (
        "http://www.mcdonalds.com.pr/api/restaurantsByCountry?country=PR",
        "http://www.mcdonalds.co.cr/api/restaurantsByCountry?country=CR",
        "http://www.mcdonalds.com.ar/api/restaurantsByCountry?country=AR",
        "http://www.mcdonalds.com.pa/api/restaurantsByCountry?country=PA",
        "http://www.mcdonalds.com.br/api/restaurantsByCountry?country=BR",
        "http://www.mcdonalds.com.ve/api/restaurantsByCountry?country=VE",
        "http://www.mcdonalds.com.mx/api/restaurantsByCountry?country=MX",
        "http://www.mcdonalds.cl/api/restaurantsByCountry?country=CL",
        "http://www.mcdonalds.com.uy/api/restaurantsByCountry?country=UY",
        "http://www.mcdonalds.com.co/api/restaurantsByCountry?country=CO",
    )

    def parse(self, response):
        data = response.text
        data.replace('" ', '"')
        data.replace(' "', '"')
        results = json.loads(data)
        results = results["content"]["restaurants"]
        for data in results:
            properties = {
                "ref": data["id"],
                "lon": float(data["longitude"]),
                "lat": float(data["latitude"]),
            }

            contact_info = data["name"][: data["name"].find("<br")]
            name = contact_info[: contact_info.find("</br")]

            properties["name"] = name
            properties["addr_full"] = data["name"][data["name"].find("<small>") : -8][
                8:
            ]

            yield GeojsonPointItem(**properties)
