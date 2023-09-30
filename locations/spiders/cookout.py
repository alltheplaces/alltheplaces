import logging
import os
import re

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points

STATES = ["NC", "AL", "GA", "KY", "MD", "MS", "SC", "TN", "VA", "WV"]


class CookoutSpider(scrapy.Spider):
    name = "cookout"
    item_attributes = {"brand": "Cookout", "brand_wikidata": "Q5166992"}
    allowed_domains = ["cookout.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        base_url = "https://cookout.com/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lng}&max_results=300&search_radius=500"

        logging.info(os.path.dirname(os.path.realpath(__file__)))
        logging.info(os.getcwd())

        with open_searchable_points("us_centroids_100mile_radius_state.csv") as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(",")
                if state in STATES:
                    url = base_url.format(lat=lat, lng=lon)
                    yield scrapy.Request(url=url, callback=self.parse)

    def store_hours(self, store_hours):
        m = re.findall(r"<tr><td>(\w*)<\/td><td><time>([0-9: APM-]*)</time></td></tr>", store_hours)

        day_groups = []
        this_day_group = dict()
        for day, hours_together in m:
            day = day[:2]
            h = re.findall("([0-9]{1,2}):([0-9]{1,2}) ([APM]{2})", hours_together)
            (from_h, from_m, from_ap), (to_h, to_m, to_ap) = h

            from_h = int(from_h)
            if from_ap == "PM":
                from_h += 12

            to_h = int(to_h)
            if to_h == "PM":
                to_h += 12

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
        data = response.json()

        for store in data:
            properties = {
                "ref": store["id"],
                "name": store["store"],
                "website": store["url"],
                "street_address": store.get("address"),
                "city": store.get("city"),
                "state": store.get("state"),
                "postcode": store.get("zip"),
                "country": store.get("country"),
                "lon": float(store["lng"]),
                "lat": float(store["lat"]),
            }

            phone = store["phone"]
            if phone:
                properties["phone"] = phone

            hours = store.get("hours", "")
            if hours:
                properties["opening_hours"] = self.store_hours(hours)

            yield Feature(**properties)

        else:
            self.logger.info("No results")
