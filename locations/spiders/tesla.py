import re
import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class TeslaSpider(scrapy.Spider):
    name = "tesla"
    item_attributes = {"brand": "Tesla", "brand_wikidata": "Q478214"}
    allowed_domains = ["www.tesla.com"]
    start_urls = [
        "https://www.tesla.com/findus",
    ]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    download_delay = 0.5

    def parse(self, response):
        # Load the main page and then make requests using the API.
        yield scrapy.Request(
            "https://www.tesla.com/cua-api/tesla-locations?translate=en_US&usetrt=true",
            callback=self.parse_json_subrequest,
        )

    def parse_json_subrequest(self, response):
        for location in response.json():
            # Skip if "Coming Soon" - no content to capture yet
            if location.get("open_soon") == "1":
                continue

            # Skip destination chargers as they're not Tesla-operated
            if location.get("location_type") == ["destination charger"]:
                continue

            yield scrapy.Request(
                url=f"https://www.tesla.com/cua-api/tesla-location?translate=en_US&usetrt=true&id={location.get('location_id')}",
                callback=self.parse_location,
            )

    def parse_location(self, response):
        location_data = response.json()
        feature = DictParser.parse(location_data)

        feature["ref"] = location_data.get("location_id")
        feature["street_address"] = feature["street_address"].replace("<br />", ", ")

        if "supercharger" in feature.get("location_type"):
            apply_category(Categories.CHARGING_STATION, feature)
            feature["brand_wikidata"] = "Q17089620"
            feature["brand"] = "Tesla Supercharger"

        if "tesla_center_delivery" in feature.get("location_type"):
            apply_category(Categories.SHOP_CAR, feature)

        if "store" in feature.get("location_type"):
            apply_category(Categories.SHOP_CAR, feature)

        if "service" in feature.get("location_type"):
            apply_category(Categories.SHOP_CAR_REPAIR, feature)

        yield feature
