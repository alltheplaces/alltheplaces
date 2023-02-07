import json
import re

import scrapy
from geonamescache import GeonamesCache

from locations.items import Feature

US_TERRITORIES = {
    "AS": {"code": "AS", "name": "American Samoa"},
    "FM": {"code": "FM", "name": "Micronesia"},
    "GU": {"code": "GU", "name": "Guam"},
    "MH": {"code": "MH", "name": "Marshall Islands"},
    "MP": {"code": "MP", "name": "Northern Mariana Islands"},
    "PW": {"code": "PW", "name": "Palau"},
    "PR": {"code": "PR", "name": "Puerto Rico"},
    "VI": {"code": "VI", "name": "U.S. Virgin Islands"},
}


class XfinitySpider(scrapy.Spider):
    name = "xfinity"
    item_attributes = {"brand": "Xfinity", "brand_wikidata": "Q5151002"}
    allowed_domains = ["www.xfinity.com"]

    def start_requests(self):
        for state in GeonamesCache().get_us_states() | US_TERRITORIES:
            yield scrapy.http.Request(url=f"https://api-support.xfinity.com/servicecenters?location={state}")

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        days = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
        hours_list = store_hours.split(",")
        for day, day_hours in zip(days, hours_list):
            day_hours = day_hours[2:]
            hours = ""
            match = re.search(r"(\d{1,2}:\d{2}):(\d{1,2}:\d{2})", day_hours)
            if match:
                (f_hr, t_hr) = match.groups()

                hours = "{}-{}".format(f_hr, t_hr)
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
        data = response.text
        stores = json.loads(data)["locations"]

        for store in stores:
            properties = {
                "ref": store["id"],
                "name": store["locationName"],
                "opening_hours": self.store_hours(store["hours"]),
                "lat": store["yextDisplayLat"],
                "lon": store["yextDisplayLng"],
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": json.loads(data)["geo"]["country"],
                "website": store["websiteUrl"],
            }

            yield Feature(**properties)
