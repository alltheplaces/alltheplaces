import scrapy

from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class SevenElevenSESpider(scrapy.Spider):
    name = "seven_eleven_se"
    start_urls = ["https://storage.googleapis.com/public-store-data-prod/stores-seven_eleven.json"]

    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}

    def parse(self, response, **kwargs):
        for store in response.json():
            coordinates = store.get("location")
            oh = OpeningHours()
            for hours in store.get("openhours").get("standard"):
                open, close = hours.get("hours")
                oh.add_range(
                    day=DAYS[hours.get("weekday")],
                    open_time=open,
                    close_time=close,
                    time_format="%H:%M",
                )
            yield Feature(
                {
                    "ref": store.get("storeId"),
                    "name": store.get("title"),
                    "state": store.get("county"),
                    "street_address": " ".join(store.get("address")),
                    "phone": store.get("phone"),
                    "postcode": store.get("postalCode"),
                    "city": store.get("city"),
                    "website": store.get("link"),
                    "lat": coordinates.get("lat"),
                    "lon": coordinates.get("lng"),
                    "opening_hours": oh,
                    "extras": Categories.SHOP_CONVENIENCE.value,
                }
            )
