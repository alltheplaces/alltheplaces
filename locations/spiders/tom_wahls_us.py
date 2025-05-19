from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.user_agents import BROWSER_DEFAULT


class TomWahlsUSSpider(scrapy.Spider):
    name = "tom_wahls_us"
    item_attributes = {"name": "Tom Wahl's", "brand": "Tom Wahl's", "brand_wikidata": "Q7817965"}
    allowed_domains = ["tomwahls.com"]
    start_urls = ["https://www.tomwahls.com/"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Tom Wahl's has all locations in JSON-LD structured data on the homepage
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            # The locations are nested in the "department" array of the main object
            if departments := ld_obj.get("department"):
                for location in departments:
                    # Filter for FastFoodRestaurant type
                    if not location.get("@type") == "FastFoodRestaurant":
                        continue

                    yield self.parse_location(location)
            # Also check direct FastFoodRestaurant objects
            elif ld_obj.get("@type") == "FastFoodRestaurant":
                yield self.parse_location(ld_obj)

    def parse_location(self, location: dict):
        item = LinkedDataParser.parse_ld(location)
        item["branch"] = item.pop("name").removeprefix("Tom Wahl's ")

        # Set ref based on branch name or city
        item["ref"] = item.get("branch") or item.get("city")

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "burger"

        return item
