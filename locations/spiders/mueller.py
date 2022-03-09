import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class MuellerSpider(scrapy.Spider):
    name = "mueller"
    allowed_domains = ["www.mueller.de"]
    start_urls = ("https://www.mueller.de/api/ccstore/allPickupStores/",)
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        for record in store_hours:
            if record["open"]:
                opening_hours.add_range(
                    day=DAY_MAPPING[record["dayOfWeek"]],
                    open_time=record["fromTime"],
                    close_time=record["toTime"],
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        store = json.loads(response.text)

        properties = {
            "lat": store["latitude"],
            "lon": store["longitude"],
            "name": store["storeName"],
            "street": store["street"],
            "city": store["city"],
            "postcode": store["zip"],
            "country": store["country"],
            "ref": store["storeNumber"],
        }

        if store["cCStoreDtoDetails"]["openingHourWeek"]:
            hours = self.parse_hours(store["cCStoreDtoDetails"]["openingHourWeek"])
            if hours:
                properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        data = json.loads(response.text)
        stores_number = [stores["storeNumber"] for stores in data]

        for n in stores_number:
            yield scrapy.Request(
                f"https://www.mueller.de/api/ccstore/byStoreNumber/{n}/",
                callback=self.parse_stores,
            )
