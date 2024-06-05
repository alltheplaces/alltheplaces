import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PizzaHutBESpider(scrapy.Spider):
    name = "pizza_hut_be"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://api.pizzahut.be/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for data in response.json()["stores"]:
            yield scrapy.Request(f"https://api.pizzahut.be/stores/{data.get('code')}", callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()
        store = response.json().get("store")
        for ohs in store.get("openingHours"):
            open, close = ohs.get("shift1").split("/")
            oh.add_range(day=DAYS[ohs.get("dayNum") - 1], open_time=open, close_time=close)

        address_details = store.get("address")
        properties = {
            "ref": store.get("code"),
            "street_address": clean_address([address_details.get("address1"), address_details.get("address2")]),
            "name": store["name"],
            "postcode": address_details.get("zipCode"),
            "city": address_details.get("city"),
            "website": store.get("infoUrl"),
            "lat": address_details.get("coordinates").get("latitude"),
            "lon": address_details.get("coordinates").get("longitude"),
            "phone": store.get("contact").get("phone").replace("/", ""),
            "opening_hours": oh,
        }

        if store["storeType"] == "FSR":
            apply_category(Categories.RESTAURANT, properties)
        elif store["storeType"] == "DELCO":
            apply_category(Categories.FAST_FOOD, properties)

        apply_yes_no(Extras.TAKEAWAY, properties, store["takeoutStatus"]["isActive"])
        apply_yes_no(Extras.DELIVERY, properties, store["deliveryStatus"]["isActive"])

        yield Feature(**properties)
