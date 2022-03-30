# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsFISpider(scrapy.Spider):

    name = "mcdonalds_fi"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.fi"]
    start_urls = (
        "http://www.mcdonalds.fi/services/mcd/restaurantLocator?latitude=60.16985569999999&longitude=24.93837910000002&radius=200000&maxResults=10000&country=fi&language=tutustu",
    )

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2}) ([ap.m]{2})", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2}) ([ap.m]{2})", time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p." else int(h),
            int(m),
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        day_hours = [
            "HOURS_MONDAY",
            "HOURS_TUESDAY",
            "HOURS_WEDNESDAY",
            "HOURS_THURSDAY",
            "HOURS_FRIDAY",
            "HOURS_SATURDAY",
            "HOURS_SUNDAY",
        ]
        for day_hour in day_hours:
            hours = ""
            day = data[day_hour]
            short_day = day_hour[6:8]
            hours = day
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

        day_groups.append(this_day_group)

        if not day_groups:
            return None
        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00 - 23:59",
            "00:00 - 00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        results = results["features"]
        for data in results:
            properties = {
                "city": data["properties"]["address_line_3"],
                "ref": data["properties"]["id"],
                "addr_full": data["properties"]["address_line_1"],
                "phone": data["properties"]["telephone"],
                "state": data["properties"]["address_line_4"],
                "postcode": data["properties"]["postcode"],
                "name": data["properties"]["name"],
                "lat": data["geometry"]["coordinates"][1],
                "lon": data["geometry"]["coordinates"][0],
            }

            opening_hours = self.store_hours(data["properties"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
