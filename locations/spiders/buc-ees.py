# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BuceesSpider(scrapy.Spider):
    name = "buc-ees"
    item_attributes = {"brand": "Buc-ee's", "brand_wikidata": "Q4982335"}
    allowed_domains = ["buc-ees.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = [
        "https://buc-ees.com/wp-admin/admin-ajax.php?action=store_search&lat=30.26715&lng=-97.74306&autoload=1"
    ]

    def parse(self, response):
        for store in response.json():
            opening_hours = OpeningHours()

            hours_table = scrapy.Selector(text=store["hours"])
            days = hours_table.css("td:first-child::text").getall()
            hours = hours_table.css(
                "td:last-child::text, td:last-child time::text"
            ).getall()

            for day, day_hours in zip(days, hours):
                if "Closed" in day_hours:
                    continue

                (open_time, close_time) = day_hours.split(" - ")
                opening_hours.add_range(
                    day=day[0:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )

            yield GeojsonPointItem(
                ref=store["id"],
                lon=store["lng"],
                lat=store["lat"],
                name=f"Buc-ee's {store['store']}",
                addr_full=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country="US"
                if store["country"] == "United States"
                else store["country"],
                phone=store["phone"],
                opening_hours=opening_hours.as_opening_hours(),
                extras={
                    "amenity:fuel": True,
                    "fuel:diesel": True,
                    "car_wash": "carwash" in store["terms"],
                },
            )
