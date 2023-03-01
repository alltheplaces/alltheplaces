import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class QuickBELUSpider(scrapy.Spider):
    name = "quick_be_lu"
    start_urls = ["https://www.quick.be/fr/Ajax/loadRestaurantsData"]

    item_attributes = {"brand": "Quick", "brand_wikidata": "Q286494"}

    def parse(self, response, **kwargs):
        for store in response.json().get("restaurants").values():
            oh = OpeningHours()
            for day in store.get("opening_hours"):
                if day.get("opening_type") != 1:
                    continue
                oh.add_range(
                    day=DAYS[day.get("weekday_from") - 1],
                    open_time=day.get("from_hour"),
                    close_time=day.get("to_hour"),
                    time_format="%H:%M:%S",
                )
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("title"),
                    "street_address": store.get("address"),
                    "phone": store.get("telephone"),
                    "email": store.get("hr_email"),
                    "postcode": store.get("postal_code"),
                    "country": store.get("country").upper(),
                    "city": store.get("locality"),
                    "website": f"https://www.quick.be/fr/restaurant/{store.get('slug')}",
                    "lat": store.get("location_lat"),
                    "lon": store.get("location_lng"),
                    "opening_hours": oh,
                }
            )
