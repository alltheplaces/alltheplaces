# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SuperAmericaSpider(scrapy.Spider):
    name = "superamerica"
    item_attributes = {"brand": "SuperAmerica"}
    allowed_domains = ["superamerica.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "http://superamerica.com/wp-admin/admin-ajax.php?action=store_search&lat=45.0&lng=-90.0&max_results=0&search_radius=500",
    )

    def store_hours(self, store_hours):
        matches = re.findall(
            r"<tr><td>(.*?)<\/td><td><time>(.*?)<\/time><\/td><\/tr>", store_hours
        )

        day_groups = []
        this_day_group = None

        for day, hours in matches:
            day = day[:2]
            match = re.search(
                r"(\d{1,2}):(\d{2}) ([AP])M - (\d{1,2}):(\d{2}) ([AP])M", hours
            )
            (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm == "P":
                f_hr += 12
            elif f_ampm == "A" and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm == "P":
                t_hr += 12
            elif t_ampm == "A" and t_hr == 12:
                t_hr = 0

            hours = "{:02d}:{}-{:02d}:{}".format(
                f_hr,
                f_min,
                t_hr,
                t_min,
            )

            if not this_day_group:
                this_day_group = dict(from_day=day, to_day=day, hours=hours)
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day, to_day=day, hours=hours)
        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            opening_hours = day_groups[0]["hours"]
            if opening_hours == "07:00-07:00":
                opening_hours = "24/7"
        else:
            opening_hours = ""
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        data = response.json()

        for store in data:
            properties = {
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "name": store["store"],
                "phone": store["phone"],
                "ref": store["id"],
                "lon": float(store["lng"]),
                "lat": float(store["lat"]),
            }

            opening_hours = self.store_hours(store["hours"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
