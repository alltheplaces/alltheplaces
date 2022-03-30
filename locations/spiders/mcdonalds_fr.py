# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class McDonalsFRSpider(scrapy.Spider):

    name = "mcdonalds_fr"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.fr"]
    start_urls = (
        "https://prod-dot-mcdonaldsfrance-storelocator.appspot.com/api/store/nearest?center=2.331052600000021:48.8640493&limit=1000&authToken=26938DBF9169A7F39C92BDCF1BA7A&db=prod",
        "https://prod-dot-mcdonaldsfrance-storelocator.appspot.com/api/store/nearest?center=2.6830176999999367:45.2304368&limit=1000&authToken=26938DBF9169A7F39C92BDCF1BA7A&db=prod",
    )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Su", "Mo", "Th", "We", "Tu", "Fr", "Sa"]
        for day_hour in data:
            if day_hour["idx"] > 7:
                continue

            hours = ""
            start, end = (
                day_hour["value"].split("-")[0].strip(),
                day_hour["value"].split("-")[1].strip(),
            )

            short_day = weekdays[day_hour["idx"] - 1]
            hours = "{}:{}-{}:{}".format(start[:2], start[3:], end[:2], end[3:])
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
        if len(day_groups) == 1 and not day_groups[0]:
            return None
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
        match = re.search(r"(HTTPResponseLoaded\()({.*})(\))", response.text)
        if not match:
            return

        results = json.loads(match.groups()[1])
        results = results["poiList"]
        for item in results:
            data = item["poi"]
            properties = {
                "city": data["location"]["city"],
                "ref": data["id"],
                "addr_full": data["location"]["streetLabel"],
                "phone": data["datasheet"]["tel"]["number"],
                "state": data["location"]["countryISO"],
                "postcode": data["location"]["postalCode"],
                "name": data["name"],
                "lat": data["location"]["coords"]["lat"],
                "lon": data["location"]["coords"]["lon"],
                "website": "https://www.restaurants.mcdonalds.fr"
                + data["datasheet"]["web"],
            }

            opening_hours = self.store_hours(data["datasheet"]["descList"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
