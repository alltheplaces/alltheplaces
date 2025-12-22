from json import dumps, loads
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {2: "Mo", 3: "Tu", 4: "We", 5: "Th", 6: "Fr", 7: "Sa", 1: "Su"}


class VictoriassecretSpider(Spider):
    name = "victoriassecret"
    item_attributes = {"brand": "Victoria's Secret", "brand_wikidata": "Q332477"}
    allowed_domains = ["victoriassecret.com"]
    start_urls = [
        "https://www.victoriassecret.com/store-locator#storeList/US",
    ]

    async def start(self) -> AsyncIterator[FormRequest]:
        template = "https://api.victoriassecret.com/stores/v1/search?countryCode=US"

        headers = {
            "Accept": "application/json",
        }

        yield FormRequest(url=template, method="GET", headers=headers, callback=self.parse)

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse:
            store = dumps(stores)
            store_data = loads(store)
            properties = {}

            if store_data["latitudeDegrees"] == "":
                properties["lat"] = float(0)
                properties["lon"] = float(0)

            else:
                properties = {
                    "name": store_data["name"],
                    "ref": store_data["storeId"],
                    "addr_full": store_data["address"]["streetAddress1"],
                    "city": store_data["address"]["city"],
                    "state": store_data["address"]["region"],
                    "postcode": store_data["address"]["postalCode"],
                    "country": "US",
                    "phone": store_data["address"]["phone"],
                    "lat": float(store_data["latitudeDegrees"]),
                    "lon": float(store_data["longitudeDegrees"]),
                }

            hours = store_data["hours"]

            if hours:
                properties["opening_hours"] = self.process_hours(hours)

            yield Feature(**properties)

    def process_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            hr = dumps(hour)
            hrs = loads(hr)
            day = hrs["day"]
            open_time = hrs["open"]
            close_time = hrs["close"]

            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=open_time,
                close_time=close_time,
                time_format="%H:%M %p",
            )
        return opening_hours.as_opening_hours()
