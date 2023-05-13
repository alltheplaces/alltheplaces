import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class HootersSpider(scrapy.Spider):
    name = "hooters"
    item_attributes = {"brand": "Hooters", "brand_wikidata": "Q1025921"}
    allowed_domains = ["www.hooters.com"]
    start_urls = ("https://www.hooters.com/api/search_locations.json",)

    day_mapping = {
        "sun": "Su",
        "mon": "Mo",
        "tue": "Tu",
        "wed": "We",
        "thu": "Th",
        "fri": "Fr",
        "sat": "Sa",
    }

    def parse_store(self, store_json):
        city = None
        state = None
        postcode = None
        country = None
        addr_full = store_json["address"]["line-1"]
        # Only US addresses on line-2 end with a zipcode in the format "Addison, TX 75240"
        if re.search(r"\d+$", store_json["address"]["line-2"]):
            city = store_json["address"]["line-2"].split(",")[0].strip()
            state = store_json["address"]["line-2"].split(",")[1].strip()[:2].strip()
            postcode = store_json["address"]["line-2"][-5:].strip()  # Get last five characters in string
            country = "US"
        # Canadian address have the format "Edmonton, AB Canada"
        elif "Canada" in store_json["address"]["line-2"]:
            city = store_json["address"]["line-2"].split(",")[0].strip()
            state = store_json["address"]["line-2"].split(",")[1].strip()[:2]
            country = "CA"
        else:
            # For an international address just concate line-1 and line-2
            addr_full = " ".join([addr_full, store_json["address"]["line-2"]])

        # Opening hours
        opening_hours = OpeningHours()
        for day, times in (store_json["hours"] or {}).items():
            opening_hours.add_range(day, times["open"], times["close"], time_format="%H:%M:%S")

        return Feature(
            lat=store_json["latitude"],
            lon=store_json["longitude"],
            name=store_json["name"],
            addr_full=addr_full,
            city=city,
            state=state,
            country=country,
            postcode=postcode,
            phone=store_json["phone"],
            opening_hours=opening_hours,
            ref=store_json["id"],
        )

    def parse(self, response):
        response_dictionary = response.json()
        stores_array = response_dictionary["locations"]
        return list(map(self.parse_store, stores_array))
