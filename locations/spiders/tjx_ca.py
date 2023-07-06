import datetime

import scrapy

from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class TjxCASpider(scrapy.Spider):
    name = "tjx_ca"
    allowed_domains = ["tjx.com"]

    chains = {
        "90": {"brand": "HomeSense", "brand_wikidata": "Q16844433"},
        "91": {"brand": "Winners", "brand_wikidata": "Q845257"},
        "93": {"brand": "Marshalls", "brand_wikidata": "Q15903261"},
    }

    def start_requests(self):
        for lat, lon in point_locations("ca_centroids_100mile_radius.csv"):
            yield scrapy.http.FormRequest(
                url="https://marketingsl.tjx.com/storelocator/GetSearchResults",
                formdata={
                    "chain": "90,91,93",
                    "lang": "en",
                    "maxstores": "100",
                    "geolat": lat,
                    "geolong": lon,
                },
                headers={"Accept": "application/json"},
            )

    def parse_hours(self, hours):
        """Mon-Thu: 9am - 9pm, Black Friday: 8am - 10pm, Sat: 9am - 9pm, Sun: 10am - 8pm"""
        opening_hours = OpeningHours()
        hours = hours.replace("Black Friday", "Fri")

        for x in hours.split(","):
            days, hrs = x.split(":", 1)
            try:
                open_time, close_time = hrs.split("-")
            except:
                continue

            if ":" in open_time:
                open_time = datetime.datetime.strptime(open_time.strip(), "%I:%M%p").strftime("%H:%M")
            else:
                open_time = datetime.datetime.strptime(open_time.strip(), "%I%p").strftime("%H:%M")

            if ":" in close_time:
                close_time = datetime.datetime.strptime(close_time.strip(), "%I:%M%p").strftime("%H:%M")
            else:
                close_time = datetime.datetime.strptime(close_time.strip(), "%I%p").strftime("%H:%M")

            if "-" in days:
                start_day, end_day = days.split("-")
                for day in DAYS[DAYS.index(start_day.strip()) : DAYS.index(end_day.strip()) + 1]:
                    opening_hours.add_range(day[:2], open_time=open_time, close_time=close_time)

            else:
                day = days.strip()[:2]
                opening_hours.add_range(day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["Stores"]:
            properties = {
                "name": store["Name"],
                "ref": store["StoreID"],
                "street_address": ", ".join(filter(None, [store["Address"], store["Address2"]])),
                "city": store["City"],
                "state": store["State"],
                "postcode": store["Zip"],
                "country": store["Country"],
                "phone": store["Phone"],
                "lat": float(store["Latitude"]),
                "lon": float(store["Longitude"]),
            }
            properties.update(self.chains[store["Chain"]])

            hours = self.parse_hours(store["Hours"])
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
