# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class AlbertAndWalterSpider(scrapy.Spider):

    name = "albert_walter"
    item_attributes = {"brand": "Albert and Walter"}
    allowed_domains = ["www.aw.ca"]
    start_urls = ("https://web.aw.ca/api/locations/",)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        days = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")

        for day, hours in zip(days, store_hours):
            hour_intervals = []
            (f_time, t_time) = hours.split("-")
            if len(f_time) > 0 and len(t_time) > 0:
                f_ampm = f_time[-2:]
                f_hr = f_time[:2]
                t_ampm = t_time[-2:]
                t_hr = t_time[:2]

                f_hr = int(f_hr)
                t_hr = int(t_hr)
                if f_ampm == "PM":
                    f_hr += 12
                if f_ampm == "AM" and f_hr == 12:
                    f_hr -= 12

                if t_ampm == "PM":
                    t_hr += 12
                if t_ampm == "AM" and t_hr == 12:
                    t_hr -= 12

                hour_intervals.append(
                    "{}:{}-{}:{}".format(
                        f_hr,
                        f_time[3:5],
                        t_hr,
                        t_time[3:5],
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
        for data in results:
            properties = {
                "ref": data["restnum"],
                "name": data["restaurant_name"],
                "lat": data["latitude"],
                "lon": data["longitude"],
                "addr_full": data[
                    "public_address"
                ],  # data['address1'] + ' ' + data['address2'],
                "city": data["city_name"],
                "state": data["province_code"],
                "postcode": data["postal_code"],
                "phone": data["phone_number"],
                "opening_hours": self.store_hours(data["hours"]),
            }

            yield GeojsonPointItem(**properties)
