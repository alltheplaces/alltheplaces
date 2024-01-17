import binascii
import os

import scrapy
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)
from locations.user_agents import BROWSER_DEFAULT


class CarrefourPLSpider(Spider):
    name = "carrefour_pl"
    # Taken from mobile app
    start_urls = ["https://c4webservice.carrefour.pl:8080/MobileWebService/v3/Bootstrap.svc/App/Bootstrap"]

    brands = {
        "Express (Zielony)": CARREFOUR_EXPRESS,
        "Express (Pomarańczowy)": CARREFOUR_EXPRESS,
        "Hipermarket": CARREFOUR_SUPERMARKET,
        "Market": CARREFOUR_MARKET,
        "Globi": {"brand": "Globi", "category": Categories.SHOP_CONVENIENCE},
    }
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield scrapy.Request(
            self.start_urls[0],
            headers={
                # random 16 hex
                "device-key": binascii.b2a_hex(os.urandom(8)).decode("utf-8"),
                "customerid": "-1",
                "os-type-id": "1",
                "version-name": "3.7.2616",
                "version-number": "309616001",
            },
            method="POST",
        )

    def parse(self, response):
        brand_ids_to_brands = {}
        for brand in response.json()["shopTypes"]:
            brand_ids_to_brands[str(brand["shopTypeForMobile"])] = brand["displayName"]

        for location in response.json()["shops"]:
            item = DictParser.parse(location)

            brand_key = brand_ids_to_brands.get(str(location["shopTypeForMobile"]))
            if not parse_brand_and_category_from_mapping(item, brand_key, self.brands):
                continue  # bad brand

            item.pop("street")
            item["ref"] = location["shopId"]
            item["street_address"] = location["street"]
            opening_hours = OpeningHours()
            for day in DAYS_EN:
                if ("shop" + day) not in location:
                    continue
                opening_str = location["shop" + day]

                opening_str = (
                    opening_str.strip()
                    .replace(",", "")
                    .replace(".", ":")
                    .replace("-:", "-")
                    .replace(":-", "-")
                    .replace("- ", "-")
                    .replace(" -", "-")
                    .split(" ")[0]
                )
                if opening_str.lower() in ["nieczynny", "nieczynne", "zamkniete", "nd"]:
                    continue
                elif opening_str.lower() in ["24h", "całodobowy"]:
                    opening_hours.add_range(day=day, open_time="00:00", close_time="23:59")
                else:
                    segments = opening_str.split("-")
                    # add :00 if missing
                    segments = [segment + ":00" if ":" not in segment else segment for segment in segments]
                    # cap at 5 characters
                    segments = [segment[:5] for segment in segments]
                    try:
                        opening_hours.add_range(day=day, open_time=segments[0], close_time=segments[1])
                    except ValueError:
                        # The opening hours are hot garbage, so we'll just skip the most problematic ones
                        pass
            item["opening_hours"] = opening_hours.as_opening_hours()
            yield item
