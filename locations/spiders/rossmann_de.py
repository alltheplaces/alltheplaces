import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}


class RossmannDeSpider(scrapy.Spider):
    name = "rossmann_de"
    allowed_domains = ["www.rossmann.de"]
    start_urls = ("https://www.rossmann.de/de/filialen/assets/data/locations.json",)
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day]
            if store_hours[store_day]:
                open_time = store_hours[store_day][0]["openTime"]
                close_time = store_hours[store_day][0]["closeTime"]
                if open_time is None and close_time is None:
                    continue
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()
        for store in stores:
            properties = {
                "lat": stores[store]["lat"],
                "lon": stores[store]["lng"],
                "name": stores[store]["name"],
                "street": stores[store]["address"],
                "city": stores[store]["city"],
                "postcode": stores[store]["postalCode"],
                "ref": store,
                "extras": {
                    "maps_url": stores[store]["mapsUrl"],
                    "url": stores[store]["url"],
                    "region": stores[store]["region"],
                    "store_code": stores[store]["storeCode"],
                },
            }
            hours = self.parse_hours(stores[store]["openingHours"])

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
