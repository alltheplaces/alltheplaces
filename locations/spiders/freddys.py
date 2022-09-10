# -*- coding: utf-8 -*-
import csv
import datetime
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class FreddysSpider(scrapy.Spider):
    name = "freddys"
    item_attributes = {"brand": "Freddy's", "brand_wikidata": "Q5496837"}
    allowed_domains = ["freddysusa.com"]
    download_delay = 0.75

    def start_requests(self):
        today = datetime.date.today().strftime("%Y%m%d")
        nextweek = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y%m%d")
        url = "https://nomnom-prod-api.freddys.com/restaurants/near?lat={lat}&long={lng}&radius=100&limit=200&nomnom=calendars&nomnom_calendars_from={today}&nomnom_calendars_to={nextweek}&nomnom_exclude_extref=999"
        with open(
                "./locations/searchable_points/us_centroids_10mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                yield scrapy.Request(
                    url.format(
                        lat=point["latitude"],
                        lng=point["longitude"],
                        today=today,
                        nextweek=nextweek,
                    ),
                    callback=self.parse_stores,
                )

    def parse_stores(self, response):
        data = response.json()

        for store in data["restaurants"]:
            if store["telephone"] == "(505) 555-5555":
                # It seems like they have fake data in some places
                continue

            oh = OpeningHours()
            if calendar := store.get("calendars").get("calendar"):
                calendar_ranges = calendar[0].get("ranges")
                for oh_range in calendar_ranges:
                    oh.add_range(
                        oh_range.get("weekday")[:2],
                        oh_range.get("start").split(" ")[-1],
                        oh_range.get("end").split(" ")[-1],
                        time_format="%H:%M",
                    )

            properties = {
                "ref": store["id"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "name": store["name"],
                "street_address": store["streetaddress"],
                "opening_hours": oh.as_opening_hours(),
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "phone": store["telephone"],
            }

            yield GeojsonPointItem(**properties)
