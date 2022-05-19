# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class PncSpider(scrapy.Spider):
    name = "pnc"
    item_attributes = {"brand": "PNC", "brand_wikidata": "Q38928"}
    allowed_domains = ["www.pnc.com"]
    start_urls = [
        "https://apps.pnc.com/locator/search",
    ]

    def start_requests(self):
        base_url = "https://apps.pnc.com/locator-api/locator/api/v2/location/?t=1619625397878&latitude={lat}&longitude={lng}&radius=100&radiusUnits=mi&branchesOpenNow=false"

        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        branch_data = data["locations"]

        for branch in branch_data:
            if "ATM" in branch["locationType"]["locationTypeDesc"]:
                pass
            else:
                properties = {
                    "ref": branch["locationId"],
                    "name": branch["locationName"],
                    "addr_full": branch["address"]["address1"],
                    "city": branch["address"]["city"],
                    "state": branch["address"]["state"],
                    "postcode": branch["address"]["zip"],
                    "lat": branch["address"]["latitude"],
                    "lon": branch["address"]["longitude"],
                }

                yield GeojsonPointItem(**properties)
