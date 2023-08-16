import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TeslaSpider(scrapy.Spider):
    name = "tesla"
    item_attributes = {"brand": "Tesla", "brand_wikidata": "Q478214"}

    download_delay = 0.5
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def start_requests(self):
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
        if isinstance(location_data, list):
            return
        feature = DictParser.parse(location_data)
        feature["ref"] = location_data.get("location_id")
        feature["street_address"] = location_data["address_line_1"].replace("<br />", ", ")
        feature["state"] = location_data.get("province_state") or None

        if "supercharger" in location_data.get("location_type"):
            apply_category(Categories.CHARGING_STATION, feature)
            feature["brand_wikidata"] = "Q17089620"
            feature["brand"] = "Tesla Supercharger"

            # Capture capacity of the supercharger
            regex = r"(\d+) Superchargers, available 24\/7, up to (\d+kW)(<br />CCS Compatibility)?"
            regex_matches = re.findall(regex, location_data.get("chargers"))
            if regex_matches:
                for match in regex_matches:
                    capacity, output, ccs_compat = match

                    if ccs_compat:
                        feature["extras"]["socket:tesla_supercharger_ccs"] = capacity
                        feature["extras"]["socket:tesla_supercharger_ccs:output"] = output
                    else:
                        feature["extras"]["socket:tesla_supercharger"] = capacity
                        feature["extras"]["socket:tesla_supercharger:output"] = output

        if "tesla_center_delivery" in location_data.get("location_type"):
            apply_category(Categories.SHOP_CAR, feature)

        if "store" in location_data.get("location_type"):
            apply_category(Categories.SHOP_CAR, feature)

        if "service" in location_data.get("location_type"):
            apply_category(Categories.SHOP_CAR_REPAIR, feature)

        yield feature
