import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class NewYorkPublicLibrarySpider(scrapy.Spider):
    name = "new_york_public_library"
    item_attributes = {
        "brand": "The New York Public Library",
        "brand_wikidata": "Q219555",
    }
    allowed_domains = ["www.nypl.org"]
    start_urls = [
        "www.nypl.org",
    ]

    def start_requests(self):
        url = "https://refinery.nypl.org/api/nypl/locations/v1.0/locations"

        yield scrapy.http.Request(url, self.parse, method="GET")

    def parse_hours(self, location_hours):
        opening_hours = OpeningHours()
        regular_hours = location_hours["regular"]

        for week_day in regular_hours:
            day = DAY_MAPPING[week_day["day"].strip(".")]
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
        data = response.json()
        locations = data["locations"]

        for location in locations:
            coordinates = location.get("geolocation", {}).get("coordinates", {})
            if coordinates:
                lat = coordinates[1]
                lon = coordinates[0]
            else:
                lat = None
                lon = None

            properties = {
                "name": location["name"],
                "ref": location["id"],
                "street_address": location["street_address"],
                "city": location["locality"],
                "state": location["region"],
                "postcode": location["postal_code"],
                "country": "US",
                "phone": location.get("contacts", {}).get("phone"),
                "website": location.get("_links", {}).get("self", {}).get("about") or response.url,
                "lat": lat,
                "lon": lon,
            }

            hours = location.get("hours")
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield Feature(**properties)
