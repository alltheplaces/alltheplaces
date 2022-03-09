# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class RoadRangerSpider(scrapy.Spider):
    name = "road_ranger"
    item_attributes = {"brand": "Road Ranger", "brand_wikidata": "Q7339377"}
    allowed_domains = ["roadrangerusa.com"]

    start_urls = (
        "https://www.roadrangerusa.com/locations-amenities/find-a-road-ranger",
    )

    def parse(self, response):
        # scrapy.shell.inspect_response(response, self)

        for location in response.css(".store-location-row"):
            coordinates = (
                location.css(".coordinates::text")
                .extract_first()
                .strip()
                .split(":")[-1]
            )
            (lat, lon) = coordinates.split(", ")

            address = (
                location.css(".store-location-teaser__address::text")
                .extract_first()
                .strip()
            )

            amenities = location.css(".store-location-teaser__amenities").get()

            yield GeojsonPointItem(
                ref=address,
                name="Road Ranger",
                addr_full=address,
                country="US",
                lat=float(lat.strip()),
                lon=float(lon.strip()),
                extras={
                    "amenity:fuel": True,
                    "fuel:diesel": True,
                    "fuel:propane": "Propane" in amenities or None,
                    "fuel:HGV_diesel": True,
                    "hgv": True,
                },
            )
