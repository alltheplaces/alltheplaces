# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CitiSpider(scrapy.Spider):
    name = "citi"
    item_attributes = {"brand": "Citi", "brand_wikidata": "Q219508"}
    allowed_domains = ["citi.com"]
    download_delay = 1.5

    headers = {
        "Content-Type": "application/json",
        "businesscode": "GCB",
        "client_id": "4a51fb19-a1a7-4247-bc7e-18aa56dd1c40",
        "channelid": "INTERNET",
        "Accept": "application/json",
        "scope": "VISITOR",
        "countrycode": "US",
        "authority": "online.citi.com",
        "referer": "https://online.citi.com/US/ag/citibank-location-finder",
        "origin": "https://online.citi.com",
        "accept-encoding": "gzip, deflate, br",
    }

    def start_requests(self):
        payload = {
            "type": "branchesAndATMs",
            "inputLocation": None,
            "resultCount": "10000",
            "distanceUnit": "MILE",
            "findWithinRadius": "100",
        }
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius_state.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(",")
                if state not in {"AK", "HI"}:
                    payload["inputLocation"] = [float(lon), float(lat)]
                    yield scrapy.Request(
                        url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                        method="POST",
                        headers=self.headers,
                        body=json.dumps(payload),
                    )

        # Alaska and Hawaii
        for point in [[-149.318198, 62.925651], [-156.400325, 20.670266]]:
            payload["inputLocation"] = point
            payload["findWithinRadius"] = "1000"
            yield scrapy.Request(
                url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                method="POST",
                headers=self.headers,
                body=json.dumps(payload),
            )

    def parse(self, response):
        data = response.json()

        for feature in data["features"]:
            postcode = feature["properties"]["postalCode"]

            # fix 4-digit postcodes :(
            if (
                feature["properties"]["country"] == "united states of america"
                and postcode
            ):
                postcode = postcode.zfill(5)

            properties = {
                "ref": feature["id"],
                "name": feature["properties"]["name"],
                "addr_full": feature["properties"]["addressLine1"].strip(),
                "city": feature["properties"]["city"].title(),
                "state": feature["properties"]["state"].upper(),
                "postcode": postcode,
                "country": feature["properties"]["country"].title(),
                "phone": feature["properties"]["phone"],
                "lat": float(feature["geometry"]["coordinates"][1]),
                "lon": float(feature["geometry"]["coordinates"][0]),
                "extras": {"type": feature["properties"]["type"]},
            }

            yield GeojsonPointItem(**properties)
