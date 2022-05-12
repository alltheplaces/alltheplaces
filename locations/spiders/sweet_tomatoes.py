# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SweetTomatoesSpider(scrapy.Spider):
    name = "sweet_tomatoes"
    item_attributes = {"brand": "Sweet Tomatoes"}
    allowed_domains = ["sweettomatoes.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://sweettomatoes.com/wp-admin/admin-ajax.php?action=store_search&lat=37.09024&lng=-95.71289100000001&max_results=9990&search_radius=1500&autoload=1",
    )

    def store_hours(self, store_hours):
        m = re.findall(
            r"<tr><td>(\w*)<\/td><td><time>([0-9: -]*)</time></td></tr>", store_hours
        )
        day_groups = []
        this_day_group = dict()
        for day, hours_together in m:
            day = day[:2]
            h = re.findall("([0-9]{1,2}):([0-9]{1,2})", hours_together)
            (from_h, from_m), (to_h, to_m) = h

            from_h = int(from_h)
            to_h = int(to_h)

            hours = "{:02}:{}-{:02}:{}".format(
                from_h,
                from_m,
                to_h,
                to_m,
            )

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
                "ref": data["id"],
                "name": data["store"],
                "lat": data["lat"],
                "lon": data["lng"],
                "addr_full": data["address"],
                "city": data["city"],
                "state": data["state"],
                "postcode": data["zip"],
                "country": data["country"],
                "phone": data["phone"],
                "website": data["permalink"],
                "opening_hours": self.store_hours(data["hours"]),
            }

            yield GeojsonPointItem(**properties)
