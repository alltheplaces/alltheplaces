import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PizzaHutBESpider(scrapy.Spider):
    name = "pizza_hut_be"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://restaurants.pizzahut.be/api/stores"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        for data in response.json():
            yield scrapy.Request(f"https://api.pizzahut.be/stores/{data.get('id')}", callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()
        store = response.json().get("store")
        for ohs in store.get("openingHours"):
            open, close = ohs.get("shift1").split("/")
            oh.add_range(day=DAYS[ohs.get("dayNum") - 1], open_time=open, close_time=close)

        address_details = store.get("address")
        properties = {
            "ref": store.get("code"),
            "addr_full": " ".join(
                [
                    address_details.get("address1"),
                    address_details.get("address2"),
                    address_details.get("city"),
                    address_details.get("zipCode"),
                ]
            ),
            "street_address": ", ".join(filter(None, [address_details.get("address1"), address_details.get("address2")])),
            "postcode": address_details.get("zipCode"),
            "city": address_details.get("city"),
            "website": f"https://restaurants.pizzahut.be/fr/restaurant/{store.get('slug')}",
            "lat": address_details.get("coordinates").get("latitude"),
            "lon": address_details.get("coordinates").get("longitude"),
            "phone": store.get("contact").get("phone"),
            "opening_hours": oh,
        }

        yield Feature(**properties)
