import json

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FreshThymeSpider(scrapy.Spider):
    name = "freshthyme"
    item_attributes = {"brand": "Fresh Thyme", "brand_wikidata": "Q64132791"}
    allowed_domains = ["www.freshthyme.com"]
    start_urls = ["https://discover.freshthyme.com/api/v2/stores"]
    require_proxy = "US"  # Cloudflare geoblocking in use

    def parse(self, response):
        data = json.loads(response.text)["items"]
        for location in data:
            hours = location.get("store_hours")
            address = location.get("address", {})
            coordinates = location.get("location", {})
            properties = {
                "name": location["name"],
                "ref": location["id"],
                "street": clean_address([address.get(f"address{x}") for x in range(1, 4)]),
                "city": address["city"],
                "postcode": address["postal_code"],
                "state": address["province"],
                "country": "US",
                "phone": location["phone_number"],
                "website": location["external_url"],
                "lat": float(coordinates["latitude"]),
                "lon": float(coordinates["longitude"]),
                "opening_hours": self.parse_hours(hours) if hours else None,
            }
            yield Feature(**properties)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.title()
            interval = store_hours[weekday]
            if isinstance(interval, dict):
                open_time = str(interval.get("start"))
                close_time = str(interval.get("end"))
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M:%S",
                )
        return opening_hours.as_opening_hours()
