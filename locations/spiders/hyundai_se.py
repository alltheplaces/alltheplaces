import scrapy

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class HyundaiSESpider(scrapy.Spider):
    name = "hyundai_se"
    start_urls = ["https://www.hyundai.se/api/elastic-locations/contextual?category=retail"]

    item_attributes = {"brand": "Hyundai", "brand_wikidata": "Q55931"}

    def parse(self, response, **kwargs):
        for store in response.json().get("aggregations").get("locations"):
            address_details = store.get("address")
            oh = OpeningHours()
            for hours in store.get("opening_hours"):
                oh.add_range(
                    day=DAYS_EN[hours.get("open_day").capitalize()],
                    open_time=hours.get("open_time"),
                    close_time=hours.get("close_time"),
                    time_format="%H:%M",
                )
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "street_address": address_details.get("street"),
                    "phone": store.get("phone"),
                    "email": store.get("email"),
                    "postcode": address_details.get("zipcode"),
                    "website": store.get("link"),
                    "lat": address_details.get("lat"),
                    "lon": address_details.get("lng"),
                    "opening_hours": oh,
                }
            )
