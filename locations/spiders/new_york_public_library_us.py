import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class NewYorkPublicLibraryUSSpider(scrapy.Spider):
    name = "new_york_public_library_us"
    item_attributes = {"brand": "The New York Public Library", "brand_wikidata": "Q219555"}

    start_urls = [
        "https://refinery.nypl.org/api/nypl/locations/v1.0/locations",
    ]

    def parse_hours(self, location_hours):
        opening_hours = OpeningHours()
        regular_hours = location_hours["regular"]

        for week_day in regular_hours:
            day = DAYS_EN[week_day["day"].strip(".")]
            open_time = week_day["open"]
            close_time = week_day["close"]

            if open_time and close_time:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )
            else:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            if images := location.get("images"):
                item["image"] = images.get("exterior")
            if coordinates := location.get("geolocation"):
                item["lon"], item["lat"] = coordinates.get("coordinates")
            item["website"] = "https://www.nypl.org/locations/" + location["slug"]

            if hours := location.get("hours"):
                item["opening_hours"] = self.parse_hours(hours)

            yield item
