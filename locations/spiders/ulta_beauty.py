# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class UltaBeautySpider(scrapy.Spider):
    name = "ulta-beauty"
    item_attributes = {"brand": "Ulta Beauty"}
    allowed_domains = ["ulta.com", "sweetiq.com"]
    start_urls = (
        "https://api.sweetiq.com/store-locator/public/locations/582b2f2f588e96c131eefa9f?page=1&perPage=0&searchFields%5B0%5D=name&countLocations=true&clientIds%5B0%5D=57b75cf805fbd94379859661",
    )

    def store_hours(self, store_hours):
        result = "Mo"
        last_day = "Mo"
        last_period = store_hours["Mon"][0][0] + "-" + store_hours["Mon"][0][1]
        for k in DAYS:

            if len(store_hours[k]):
                period = store_hours[k][0][0] + "-" + store_hours[k][0][1]
                if period == last_period:
                    continue
                if DAYS[DAYS.index(k) - 1][:2] == last_day:
                    result += " " + last_period + "; "
                else:
                    result += (
                        "-" + DAYS[DAYS.index(k) - 1][:2] + " " + last_period + "; "
                    )
                last_period = period
                last_day = k[:2]
                result += k[:2]
            else:
                if k == "Mo":
                    result = ""
                    last_period = ""
                if last_period:
                    if DAYS[DAYS.index(k) - 1][:2] == last_day:
                        result += " " + last_period + "; "
                    else:
                        result += (
                            "-" + DAYS[DAYS.index(k) - 1][:2] + " " + last_period + "; "
                        )
                last_period = ""
                last_day = ""

        if last_day != "Su" and last_period != "":
            result += "-Su"

        result += " " + last_period
        return result

    def parse(self, response):
        shops = json.loads(response.text)

        for shop in shops["records"]:
            o = OpeningHours()
            for d, ranges in shop["hoursOfOperation"].items():
                for r in ranges:
                    o.add_range(d[:2], r[0], r[1])

            yield GeojsonPointItem(
                website=shop["website"],
                ref=shop["branch"],
                opening_hours=o.as_opening_hours(),
                phone=shop["phone"],
                addr_full=shop["address"],
                postcode=shop["postalCode"],
                city=shop["city"],
                state=shop["province"],
                country=shop["country"],
                lat=shop["geo"][1],
                lon=shop["geo"][0],
            )
