from urllib.parse import urljoin

import scrapy

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingSESpider(scrapy.Spider):
    name = "burger_king_se"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://bk-se-ordering-api.azurewebsites.net/api/v2/restaurants?latitude=59.330311012767446&longitude=18.068330468145753&radius=99900000&top=100000"
    ]
    restaurants_url = "https://bk-se-ordering-api.azurewebsites.net/api/v2/restaurants/"
    website_template = "https://burgerking.se/restauranger/{slug}"

    def parse(self, response):
        for store in response.json().get("data"):
            yield scrapy.Request(
                url=urljoin(self.restaurants_url, store.get("slug")),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json().get("data")
        coords = store.get("storeLocation").get("coordinates")
        oh = OpeningHours()
        for day in store.get("storeOpeningHours"):
            hours = day.get("hoursOfBusiness")
            oh.add_range(
                DAYS_EN.get(day.get("dayOfTheWeek")), hours.get("opensAt"), hours.get("closesAt"), "%Y-%m-%dT%H:%M:%S"
            )
        yield Feature(
            {
                "ref": store.get("id"),
                "name": store.get("storeName"),
                "street_address": store.get("storeAddress"),
                "lat": coords.get("latitude"),
                "lon": coords.get("longitude"),
                "website": self.website_template.format(slug=store.get("slug")),
                "opening_hours": oh.as_opening_hours(),
                "extras": {
                    "drive_through": "yes" if store.get("hasDriveThru") is True else "no",
                    "delivery": "yes" if store.get("isDelivery") is True else "no",
                },
            }
        )
