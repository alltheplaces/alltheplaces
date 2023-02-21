from datetime import datetime

import scrapy

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class SystembolagetSESpider(scrapy.Spider):
    name = "systembolaget_se"
    item_attributes = {"brand": "Systembolaget", "brand_wikidata": "Q1476113"}
    start_urls = ["https://api-systembolaget.azure-api.net/sb-api-ecommerce/v1/sitesearch/site?includePredictions=true"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"ocp-apim-subscription-key": "cfc702aed3094c86b92d6d4ff7a54c84"}}

    def parse(self, response, **kwargs):
        for store in response.json().get("siteSearchResults"):
            if store.get("isAgent"):
                continue
            coordinates = store.get("position")
            oh = OpeningHours()
            for opening_hour in store.get("openingHours"):
                day_of_week = sanitise_day(datetime.fromisoformat(opening_hour.get("date")).strftime("%A"))
                start, end = opening_hour.get("openFrom"), opening_hour.get("openTo")
                if start == end:
                    continue
                oh.add_range(
                    day_of_week, start, end, time_format="%H:%M:%S"
                )

            yield Feature(
                {
                    "ref": store.get("siteId"),
                    "name": store.get("displayName"),
                    "street_address": store.get("streetAddress"),
                    "postcode": store.get("postalCode"),
                    "city": store.get("city"),
                    "state": store.get("county"),
                    "lat": coordinates.get("latitude"),
                    "lon": coordinates.get("longitude"),
                    "opening_hours": oh,
                }
            )
