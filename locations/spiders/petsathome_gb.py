# -*- coding: utf-8 -*-
import scrapy
import json
from locations.geo import point_locations
from locations.linked_data_parser import LinkedDataParser
from scrapy.http import FormRequest


class PetsAtHomeGBSpider(scrapy.Spider):
    name = "petsathome_gb"
    item_attributes = {
        "brand": "Pets at Home",
        "brand_wikidata": "Q7179258",
    }
    download_delay = 0.2

    def start_requests(self):
        headers = {"X-Requested-With": "XMLHttpRequest"}
        url = "https://community.petsathome.com/models/utils.cfc"
        for (lat, lon) in point_locations("eu_centroids_20km_radius_country.csv", "UK"):
            form_data = {
                "method": "functionhandler",
                "returnFormat": "json",
                "event": "webproperty.storelocator",
                "lat": str(lat),
                "lng": str(lon),
                "radius": "50",
                "companyID": "any",
                "active": "true",
            }
            yield FormRequest(
                url, callback=self.parse_func, formdata=form_data, headers=headers
            )

    def parse_func(self, response):
        for node in json.loads(response.body)["data"]:
            if "groom-room" not in node["slug"]:
                yield scrapy.Request("https://community.petsathome.com" + node["slug"])

    def parse(self, response):
        return LinkedDataParser.parse(response, "PetStore")
