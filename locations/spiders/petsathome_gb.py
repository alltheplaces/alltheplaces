# -*- coding: utf-8 -*-
import scrapy
import json
import csv
from locations.linked_data_parser import LinkedDataParser
from scrapy.http import FormRequest


# This method could be moved into library code and documented, tested etc, supports calls of the form:
# get_locations("eu_centroids_40km_radius_country.csv")
# get_locations("eu_centroids_40km_radius_country.csv", ["GB", "IE"])
# get_locations("us_centroids_50mile_radius_state.csv", "NY")
def get_locations(areas_csv_file, area_field_filter=None):
    def get_key(row, keys):
        for key in keys:
            if row.get(key):
                return row[key]
        return None

    if area_field_filter and type(area_field_filter) is not list:
        area_field_filter = [area_field_filter]
    with open("./locations/searchable_points/{}".format(areas_csv_file)) as points:
        for row in csv.DictReader(points):
            lat, lon = row["latitude"], row["longitude"]
            if not lat or not lon:
                raise Exception("missing lat/lon in file")
            area = get_key(row, ["country", "territory", "state"])
            if area_field_filter:
                if not area:
                    raise Exception(
                        "trying to perform area filter on file with no area support"
                    )
                if area not in area_field_filter:
                    continue
            yield lat, lon


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
        for (lat, lon) in get_locations("eu_centroids_20km_radius_country.csv", "UK"):
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
