# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class TractorSupplySpider(scrapy.Spider):
    name = "tractorsupply"
    item_attributes = {"brand": "Tractor Supply", "brand_wikidata": "Q15109925"}
    allowed_domains = ["tractorsupply.com"]
    download_delay = 1.5
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; CrOS aarch64 14324.72.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.91 Safari/537.36",
    }
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": headers,
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"
        },
    }

    def start_requests(self):
        base_url = "https://www.tractorsupply.com/wcs/resources/store/10151/zipcode/fetchstoredetails?responseFormat=json&latitude={lat}&longitude={lng}"

        with open(
            "./locations/searchable_points/us_centroids_25mile_radius.csv"
        ) as points:
            next(points)  # ignore CSV header
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        day_hour = hours.split("|")

        opening_hours = OpeningHours()

        for dh in day_hour:
            try:
                day = DAYS_NAME[dh.split("=")[0]]
                hr = dh.split("=")[1]
                open_time, close_time = hr.split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()
        store_data = data["storesList"]

        for store in store_data:

            properties = {
                "ref": store["stlocId"],
                "name": store["storeName"],
                "addr_full": store["addressLine"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zipCode"],
                "phone": store["phoneNumber"],
                "lat": store["latitude"],
                "lon": store["longitude"],
            }

            hours = self.parse_hours(store["storeHours"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
