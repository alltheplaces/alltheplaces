# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class SevenElevenSpider(scrapy.Spider):
    name = "seven_eleven_ca"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    allowed_domains = ["yext.com"]

    start_urls = (
        "https://liveapi.yext.com/v2/accounts/me/locations?api_key=4c8292a53c2dae5082ba012bdf783295&v=20180210&limit=50&offset=0",
    )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = hours.split(",")
        for hour in hours:
            day, open_hour, open_minute, close_hour, close_minute = hour.split(":")
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time="{}:{}".format(open_hour, open_minute),
                close_time="{}:{}".format(close_hour, close_minute),
                time_format="%H:%M",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        stores = data["response"]["locations"]

        if stores:
            for store in stores:
                if store["closed"]["isClosed"]:
                    continue  # permanently closed

                properties = {
                    "name": store["locationName"],
                    "ref": store["id"],
                    "addr_full": store["address"],
                    "city": store["city"],
                    "state": store["state"],
                    "postcode": store["zip"],
                    "country": store["countryCode"],
                    "phone": store.get("phone"),
                    "website": "http://7eleven.ca/store-locator/" + str(store["id"]),
                    "lat": store["yextDisplayLat"],
                    "lon": store["yextDisplayLng"],
                }

                hours = self.parse_hours(store["hours"])
                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)

            offset = int(re.search(r"offset=(\d+)", response.url).groups()[0])
            url = response.urljoin(
                response.url.replace(
                    "offset={}".format(offset), "offset={}".format(offset + 50)
                )
            )
            yield scrapy.Request(url)
