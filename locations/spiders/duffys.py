import scrapy
from scrapy.http import JsonRequest

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class DuffysSpider(scrapy.Spider):
    name = "duffys"
    item_attributes = {"brand": "Duffys", "extras": {"amenity": "restaurant", "cuisine": "american"}}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.duffysmvp.com/api/app/nearByLocations",
            data={"latitude": "26.6289791", "longitude": "-80.0724384"},
        )

    def parse(self, response):
        results = response.json()

        for store in results:
            address_results = store.get("address")

            oh_str = store.get("hoursOfOperation").strip().replace("Daily", "Mo-Su")

            oh = OpeningHours()
            for rule in oh_str.split(", "):
                days, times = rule.split(": ")
                start_day, end_day = days.split("-")
                start_time, end_time = times.split(" - ")

                # eg 2am -> 02am
                if len(start_time) == 3:
                    start_time = "0" + start_time
                if len(end_time) == 3:
                    end_time = "0" + end_time

                # eg 12am -> 12:00am
                if ":" not in start_time:
                    start_time = start_time[:2] + ":00" + start_time[2:]
                if ":" not in end_time:
                    end_time = end_time[:2] + ":00" + end_time[2:]

                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)

                for day in day_range(start_day, end_day):
                    oh.add_range(day, start_time, end_time, time_format="%I:%M%p")

            properties = {
                "ref": store.get("code"),
                "name": store.get("name"),
                "street_address": address_results.get("address1"),
                "city": address_results.get("city"),
                "country": address_results.get("country"),
                "phone": address_results.get("phone"),
                "state": address_results.get("stateProvince"),
                "postcode": address_results.get("postalCode"),
                "opening_hours": oh.as_opening_hours(),
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
            }

            yield Feature(**properties)
