# -*- coding: utf-8 -*-
import re
import datetime

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thur": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
    "Mon – Fri": "Mo-Fr",
    "Mon – Sat": "Mo-Sa",
    "Mon – Thu": "Mo-Th",
    "Fri – Sat": "Fr-Sa",
    "Thu – Fri": "Th-Fr",
    "Mon – Wed": "Mo-We",
    "Thu – Sat": "Th-Sa",
}


class JcrewSpider(scrapy.Spider):
    name = "jcrew"
    item_attributes = {"brand": "J. Crew"}
    allowed_domains = [
        "stores.jcrew.com",
        "stores.factory.jcrew.com",
        "stores.madewell.com",
    ]
    start_urls = [
        "https://stores.jcrew.com/en/api/v2/stores.json",
        "https://stores.factory.jcrew.com/en/api/v2/stores.json",
        "https://stores.madewell.com/en/api/v2/stores.json",
    ]

    def parse_hours(self, hours):
        o_hours = []

        for i in hours:
            times = re.search(r"(.+)&#8211;\s+(.+)", i["hours"]).groups()

            start = times[0].replace(" ", "")
            end = times[1].replace(" ", "")

            start = datetime.datetime.strptime(start, "%I:%M%p").strftime("%H:%M")
            end = datetime.datetime.strptime(end, "%I:%M%p").strftime("%H:%M")
            days = DAY_MAPPING[i["days"]]

            if days == "Su":
                sunday_hours = "%s %s-%s" % (days, start, end)
            else:
                opening_hours = "%s %s-%s" % (days, start, end)
                o_hours.append(opening_hours)

        o_hours.append(sunday_hours)

        return "; ".join(o_hours)

    def parse(self, response):
        data = response.json()

        brand = None
        if re.search(r"stores.(.\w+)", response.url).groups()[0] == "factory":
            brand = "J.Crew Factory"
        elif re.search(r"stores.(.\w+)", response.url).groups()[0] == "jcrew":
            brand = "J.Crew"
        else:
            brand = "Madewell"

        for place in data["stores"]:
            properties = {
                "ref": place["id"],
                "name": place["name"],
                "addr_full": place["address_1"],
                "city": place["city"],
                "state": place["state"],
                "postcode": place["postal_code"],
                "country": place["country_code"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "phone": place["phone_number"],
                "website": response.urljoin(place["url"]),
                "brand": brand,
            }

            hours = place["regular_hour_ranges"]

            try:
                h = self.parse_hours(hours)
                properties["opening_hours"] = h
            except:
                pass

            yield GeojsonPointItem(**properties)
