from urllib.parse import urlencode

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}

BASE_URL = "https://onmyj41p3c.execute-api.us-west-2.amazonaws.com/prod/v2.1/getStoresByCoordinates?"


class TMobileUSSpider(scrapy.Spider):
    name = "tmobile_us"
    item_attributes = {
        "brand": "T-Mobile",
        "brand_wikidata": "Q3511885",
        "country": "US",
    }
    allowed_domains = ["www.t-mobile.com"]
    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("day")]
            open_time = store_day.get("opens")
            close_time = store_day.get("closes")
            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def start_requests(self):
        url = BASE_URL

        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(",")

                params = {
                    "latitude": "{}".format(lat),
                    "longitude": "{}".format(lon),
                    "count": "1000",
                    "radius": "25",
                    "ignoreLoadingBar": "false",
                }

                yield scrapy.http.Request(url + urlencode(params), callback=self.parse)

    def parse(self, response):
        data = response.json()

        for store in data:
            properties = {
                "name": store.get("name"),
                "ref": store["id"],
                "street_address": store["location"]["address"]["streetAddress"],
                "city": store["location"]["address"]["addressLocality"],
                "state": store["location"]["address"]["addressRegion"],
                "postcode": store["location"]["address"]["postalCode"],
                "phone": store.get("telephone"),
                "website": store.get("url") or response.url,
                "lat": store["location"]["latitude"],
                "lon": store["location"]["longitude"],
            }

            hours = self.parse_hours(store.get("hours", []))
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
