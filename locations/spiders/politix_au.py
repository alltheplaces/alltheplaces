import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.google_url import extract_google_position
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PolitixAUSpider(Spider):
    name = "politix_au"
    item_attributes = {"brand": "Politix", "brand_wikidata": "Q126166036"}
    start_urls = [
        "https://www.politix.com.au/on/demandware.store/Sites-politix_au-Site/en_AU/PolitixStores-GetAllStores?countryCode=AU"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            # MYER/DAVID_JONES also appear
            if location["storeType"]["value"] == "POLITIX_STORES":
                item = DictParser.parse(location)
                hours_string = re.sub(
                    r"\s+", " ", location["storeHours"].replace("</p>", "").replace("<p>", "")
                ).strip()
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)
                if " (" in item["name"]:
                    item["name"] = item["name"].split(" (")[0]
                yield item
