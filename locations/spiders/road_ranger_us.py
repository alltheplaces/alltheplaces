import re

import scrapy

from locations.items import Feature


class RoadRangerUSSpider(scrapy.Spider):
    name = "road_ranger_us"
    item_attributes = {"brand": "Road Ranger", "brand_wikidata": "Q7339377"}
    allowed_domains = ["roadrangerusa.com"]

    start_urls = ("https://www.roadrangerusa.com/locations-amenities/find-a-road-ranger",)

    def parse(self, response):
        for location in response.css(".store-location-row"):
            if m := re.search(r"Coordinates:\s+(-?\d+\.\d+), (-?\d+\.\d+)", location.get()):
                lat, lon = m.groups()
            else:
                lat, lon = None

            address = location.css(".store-location-teaser__address::text").extract_first().strip()

            amenities = location.css(".store-location-teaser__amenities").get()

            yield Feature(
                ref=address,
                name="Road Ranger",
                addr_full=address,
                country="US",
                lat=lat,
                lon=lon,
                extras={
                    "amenity": "fuel",
                    "fuel:diesel": "yes",
                    "fuel:propane": "yes" if "Propane" in amenities else "",
                    "fuel:HGV_diesel": "yes",
                    "hgv": "yes",
                },
            )
