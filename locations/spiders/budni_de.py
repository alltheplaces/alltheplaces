from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class BudniDESpider(scrapy.Spider):
    name = "budni_de"
    allowed_domains = ["www.budni.de"]
    start_urls = ["https://www.budni.de/api/infra/branches"]
    item_attributes = {"brand": "Budni", "brand_wikidata": "Q1001516"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location_data in response.json():
            yield Feature(
                {
                    "ref": location_data["id"],
                    "name": location_data["displayName"],
                    "street_address": location_data["street"],
                    "city": location_data["city"],
                    "postcode": location_data["zip"],
                    "country": "DE",
                    "lat": location_data["location"]["lat"],
                    "lon": location_data["location"]["lon"],
                    "website": f'https://www.budni.de{location_data["navigationPath"]}',
                    "image": location_data["headerImage"],
                    "opening_hours": self.parse_opening_hours(location_data["openingHours"]),
                    "email": location_data["email"],
                }
            )

    @staticmethod
    def parse_opening_hours(hours_definition):
        oh = OpeningHours()
        for day, interval in hours_definition.items():
            open_time, close_time = interval.strip().strip(" Uhr").split("-")
            oh.add_range(day.title(), open_time.replace(":", "."), close_time.replace(":", "."), time_format="%H.%M")
        return oh
