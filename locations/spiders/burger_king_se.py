from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingSESpider(Spider):
    name = "burger_king_se"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://bk-se-ordering-api.azurewebsites.net/api/v2/restaurants?latitude=59.330311012767446&longitude=18.068330468145753&radius=99900000&top=100000"
    ]
    restaurants_url = "https://bk-se-ordering-api.azurewebsites.net/api/v2/restaurants/"
    website_template = "https://burgerking.se/restauranger/{slug}"

    def parse(self, response):
        for store in response.json().get("data"):
            yield Request(
                url=urljoin(self.restaurants_url, store.get("slug")),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json().get("data")
        coords = store.get("storeLocation").get("coordinates")

        properties = {
            "ref": store.get("id"),
            "name": store.get("storeName"),
            "street_address": store.get("storeAddress"),
            "lat": coords.get("latitude"),
            "lon": coords.get("longitude"),
            "website": self.website_template.format(slug=store.get("slug")),
            "opening_hours": OpeningHours(),
        }

        for day in store.get("storeOpeningHours"):
            hours = day.get("hoursOfBusiness")
            properties["opening_hours"].add_range(
                DAYS_EN.get(day.get("dayOfTheWeek")), hours.get("opensAt"), hours.get("closesAt"), "%Y-%m-%dT%H:%M:%S"
            )

        apply_category(Categories.FAST_FOOD, properties)
        apply_yes_no(Extras.DRIVE_THROUGH, properties, store.get("hasDriveThru") is True, False)
        apply_yes_no(Extras.DELIVERY, properties, store.get("isDelivery") is True, False)

        yield Feature(**properties)
