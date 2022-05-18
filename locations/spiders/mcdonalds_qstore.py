# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonalsQStoreSpider(scrapy.Spider):

    name = "mcdonalds_qstore"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["mcdonalds.com.au", "mcdonalds.co.nz"]
    start_urls = (
        "https://mcdonalds.com.au/data/store",
        "https://mcdonalds.co.nz/data/store",
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
        day_hours = data["store_trading_hour"]
        for day_hour in day_hours:
            hours = ""
            day, start, end = day_hour[0], day_hour[1], day_hour[2]
            if day == "Day":
                continue
            short_day = day[:2]
            hours = "{}:{}-{}:{}".format(start[:2], start[2:], end[:2], end[2:])
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
            "00:00-23:59",
            "00:00-00:00",
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
        for data in results:
            properties = {
                "city": data["store_suburb"],
                "ref": data["store_code"],
                "addr_full": data["store_address"],
                "phone": data["store_phone"],
                "state": data["store_state"],
                "postcode": data["store_postcode"],
                "name": data["title"],
            }

            lat_lon = data["store_geocode"]
            if not lat_lon:
                continue
            properties["lon"] = lat_lon.split(",")[0].strip()
            properties["lat"] = lat_lon.split(",")[1].strip()

            opening_hours = self.store_hours(data)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
