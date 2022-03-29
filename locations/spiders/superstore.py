# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SuperStoreSpider(scrapy.Spider):

    name = "super_store"
    item_attributes = {"brand": "Real Canadian Superstore"}
    allowed_domains = ["www.realcanadiansuperstore.ca/"]
    start_urls = (
        "https://www.realcanadiansuperstore.ca/store-locator/locations/all?showNonShoppable=true&_=1513507990972",
    )

    def store_hours(self, store_hours):
        if "24 hours" in store_hours:
            return "24/7"
        day_groups = []
        this_day_group = None
        days = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")

        for day in days:
            hour_intervals = []
            (f_time, t_time) = store_hours.split("-")
            if len(f_time) > 0 and len(t_time) > 0:
                f_ampm = f_time[-2:]
                f_hr = re.search(r"([0-9]{1,2}):", f_time).group(1)
                t_ampm = t_time[-2:]
                t_hr = re.search(r"([0-9]{1,2}):", t_time).group(1)
                f_min = re.search(r":([0-9]{1,2})", f_time).group(1)
                t_min = re.search(r":([0-9]{1,2})", t_time).group(1)

                f_hr = int(f_hr)
                t_hr = int(t_hr)
                if f_ampm == "pm":
                    f_hr += 12
                if f_ampm == "am" and f_hr == 12:
                    f_hr -= 12

                if t_ampm == "pm":
                    t_hr += 12
                if t_ampm == "am" and t_hr == 12:
                    t_hr -= 12

                hour_intervals.append(
                    "{}:{}-{}:{}".format(
                        f_hr,
                        f_min,
                        t_hr,
                        t_min,
                    )
                )
            hours = ",".join(hour_intervals)
            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        for data in results["searchResult"]:
            properties = {
                "ref": data["details"]["storeID"],
                "name": data["details"]["storeName"],
                "lat": data["lat"],
                "lon": data["lng"],
                "addr_full": data["details"]["streetAddress"],
                "city": data["details"]["city"],
                "state": data["details"]["province"],
                "postcode": data["details"]["postalCode"],
                "website": data["details"]["url"],
            }

            if "todaysHours" in data["details"]:
                if data["details"]["todaysHours"]:
                    properties["opening_hours"] = self.store_hours(
                        data["details"]["todaysHours"]
                    )

            yield GeojsonPointItem(**properties)
