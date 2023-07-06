import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class PennyDESpider(scrapy.Spider):
    name = "penny_de"
    item_attributes = {"brand": "Penny", "brand_wikidata": "Q284688"}
    allowed_domains = ["penny.de"]
    start_urls = ("https://www.penny.de/.rest/market",)

    def parse_hours(self, store_info):
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            opening_time = store_info[f"opensAt{day}"]
            closing_time = store_info[f"closesAt{day}"]
            if any([opening_time == "", closing_time == ""]):
                continue
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=opening_time,
                close_time=closing_time,
                time_format="%H:%M",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["results"]:
            properties = {
                "name": store["marketName"],
                "ref": store["marketId"],
                "addr_full": store["street"],
                "city": store["city"],
                "postcode": store["zipCode"],
                "country": "DE",
                "lat": float(store["latitude"]),
                "lon": float(store["longitude"]),
                "extras": {"addr:housenumber": store["streetNumber"]},
            }
            hours = self.parse_hours(store)

            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
