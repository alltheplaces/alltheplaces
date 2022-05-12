# -*- coding: utf-8 -*-
import csv
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class KumAndGoSpider(scrapy.Spider):
    name = "kum_and_go"
    item_attributes = {"brand": "Kum & Go", "brand_wikidata": "Q6443340"}
    allowed_domains = ["kumandgo.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius_state.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["state"] in (
                    "IA",
                    "AR",
                    "CO",
                    "MN",
                    "MO",
                    "MT",
                    "NE",
                    "ND",
                    "OK",
                    "SD",
                    "WY",
                ):
                    yield scrapy.Request(
                        f'https://www.kumandgo.com/wordpress/wp-admin/admin-ajax.php?action=store_search&lat={point["latitude"]}&lng={point["longitude"]}&max_results=100&search_radius=100',
                    )

    def parse(self, response):
        result = json.loads(response.text)
        for store in result:

            yield GeojsonPointItem(
                ref=store["id"],
                lon=store["lng"],
                lat=store["lat"],
                addr_full=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country=store["country"],
                phone=store["phone"],
                website=store["permalink"],
            )
