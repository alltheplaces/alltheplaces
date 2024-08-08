import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class GulfOilNLSpider(scrapy.Spider):
    name = "gulf_oil_nl"
    start_urls = ["https://www.gulftankstationsenviemretail.nl/wp-content/themes/gulf-stations/gulf-map/json.php"]
    item_attributes = {"brand": "Gulf", "brand_wikidata": "Q5617505"}

    def parse(self, response, **kwargs):
        for store in response.json():
            yield scrapy.Request(
                f"https://www.gulftankstationsenviemretail.nl/wp-content/themes/gulf-stations/gulf-map/json.php?station_id={store.get('id')}",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store_info = response.json().get("info")

        oh = OpeningHours()
        for key, value in store_info.items():
            if "from" in key:
                day = key.split("_")[1]
                open_time = value.strip()
                close_time = store_info.get(f"open_{day}_till").strip()

                if not open_time or not close_time:
                    continue

                oh.add_range(day=sanitise_day(day), open_time=open_time, close_time=close_time, time_format="%H:%M")

        yield Feature(
            {
                "ref": store_info.get("id"),
                "branch": store_info.get("name"),
                "street_address": " ".join([store_info.get("house_number"), store_info.get("street")]),
                "street": store_info.get("street"),
                "housenumber": store_info.get("house_number"),
                "phone": store_info.get("phone"),
                "postcode": store_info.get("postal_code"),
                "city": store_info.get("city"),
                "website": store_info.get("link"),
                "lat": float(store_info.get("y-cords")),
                "lon": float(store_info.get("x-cords")),
                "opening_hours": oh,
                "extras": Categories.FUEL_STATION.value,
            }
        )
