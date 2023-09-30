import csv
import json

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class KumAndGoSpider(scrapy.Spider):
    name = "kum_and_go"
    item_attributes = {"brand": "Kum & Go", "brand_wikidata": "Q6443340"}
    allowed_domains = ["kumandgo.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        with open_searchable_points("us_centroids_100mile_radius_state.csv") as points:
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
            yield Feature(
                ref=store["id"],
                lon=store["lng"],
                lat=store["lat"],
                street_address=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country=store["country"],
                phone=store["phone"],
                website=store["permalink"],
            )
