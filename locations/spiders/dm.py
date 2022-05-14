import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa", 7: "Su"}

COUNTRY_MAPPING = {"DE": "Germany"}


class DmSpider(scrapy.Spider):
    name = "dm"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    allowed_domains = ["store-data-service.services.dmtech.com"]
    start_urls = [
        "https://store-data-service.services.dmtech.com/stores/bbox/"
        "85.999%2C-179.999%2C-89.999%2C179.999"
    ]
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("weekDay")]
            open_time = store_day["timeRanges"][0]["opening"]
            close_time = store_day["timeRanges"][0]["closing"]

            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()
        for store in stores["stores"]:
            if store["localeCountry"] in COUNTRY_MAPPING:
                properties = {
                    "country": COUNTRY_MAPPING[store["localeCountry"]],
                    "ref": store["storeNumber"],
                    "phone": store["phone"],
                    "name": store["address"]["name"],
                    "street": store["address"]["street"],
                    "postcode": store["address"]["zip"],
                    "city": store["address"]["city"],
                    "lat": store["location"]["lat"],
                    "lon": store["location"]["lon"],
                }
                hours = self.parse_hours(store["openingHours"])
                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)
