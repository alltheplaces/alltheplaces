# -*- coding: utf-8 -*-
import csv
import json
import re

import scrapy


from locations.items import GeojsonPointItem


states = ["AL", "FL", "GA", "NC", "SC", "TN", "VA"]


class PublixSpider(scrapy.Spider):
    name = "publix"
    item_attributes = {"brand": "Publix", "brand_wikidata": "Q672170"}
    allowed_domains = ["publix.com"]
    download_delay = 0.2

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_10mile_radius_state.csv"
        ) as points:
            for row in csv.DictReader(points):
                if row["state"] not in states:
                    continue
                latitude = row["latitude"]
                longitude = row["longitude"]
                url = f"https://services.publix.com/api/v1/storelocation?latitude={latitude}&longitude={longitude}"
                yield scrapy.Request(url, headers={"Accept": "application/json"})

    def parse(self, response):
        for row in json.loads(response.body)["Stores"]:
            ref = row["KEY"]
            properties = {
                "lat": row["CLAT"],
                "lon": row["CLON"],
                "ref": ref,
                "name": row["NAME"],
                "addr_full": row["ADDR"],
                "city": row["CITY"],
                "state": row["STATE"],
                "postcode": row["ZIP"],
                "opening_hours": row["STRHOURS"],
                "phone": row["PHONE"],
                "extras": {"fax": row["FAX"]},
                "website": f"https://www.publix.com/locations/{ref}",
            }
            yield GeojsonPointItem(**properties)
