import json

import scrapy

from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class KikSpider(scrapy.Spider):
    name = "kik"
    item_attributes = {"brand": "Kik", "brand_wikidata": "Q883965"}
    allowed_domains = ["kik.de"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.kik.de/storefinderAssets"]

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        point_files = "eu_centroids_120km_radius_country.csv"
        countries = self.find_between(response.text, "countries: ", "list").replace("},", "}").replace("'", '"')
        for country in json.loads(countries):
            for lat, lon in point_locations(point_files, country.upper()):
                yield scrapy.Request(
                    f"https://storefinder-microservice.kik.de/storefinder/results.json?lat={lat}&long={lon}&country={country}&distance=130",
                    callback=self.parse_store,
                    cb_kwargs={"country": country},
                )

    def parse_store(self, response, country):
        data = response.json().get("stores")[0].get("results")
        for _, store in data.items():
            oh = OpeningHours()
            if store.get("opening_times"):
                openHours = [
                    f'{row.split(":", 1)[0][:2]} {row.split(":", 1)[1]}'
                    for row in store.get("opening_times").split("*")
                    if row.split(":", 1)[1] != "  - "
                ]
                oh.from_linked_data({"openingHours": openHours})

            properties = {
                "ref": store.get("filiale"),
                "street_address": store.get("address"),
                "city": store.get("city"),
                "postcode": store.get("zip"),
                "country": country.upper(),
                "lat": float(store.get("latitude")),
                "lon": float(store.get("longitude")),
                "opening_hours": oh.as_opening_hours(),
            }

            yield GeojsonPointItem(**properties)
