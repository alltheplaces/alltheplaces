# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonalsLocatorSpider(scrapy.Spider):

    name = "mcdonalds_locator"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.com.hk", "www.mcdonalds.ie", "www5.mcdonalds.com"]
    start_urls = (
        "http://www.mcdonalds.com.hk/googleapps/GoogleHongKongSearchAction.do?method=searchLocation&searchTxtLatlng=(22.25%2C%20114.16669999999999)&actionType=searchRestaurant&country=hk&language=en",
        "http://www.mcdonalds.ie/googleapps/GoogleSearchAction.do?method=searchLocation&searchTxtLatlng=(54.0551962%2C%20-8.728650000000016)&actionType=searchRestaurant&language=en&country=ir",
        "http://www5.mcdonalds.com/googleapps/GoogleSearchTaiwanAction.do?method=searchLocation&searchTxtLatlng=(24.5711502%2C%20120.81543579999993)&actionType=filterRestaurant&language=zh&country=tw",
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
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]
        if "timeings" not in data.keys():
            return None
        day_hours = data["timeings"]

        index = 0
        for day_hour in day_hours:
            hours = ""
            start = day_hour["openTime"]
            if not start:
                continue
            end = day_hour["closeTime"]

            short_day = weekdays[index]
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

            index = index + 1

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

    def parse_address(self, address):
        address = address["address"]
        match = re.search(r"<p>(.*)<", address)

        if not match:
            match = re.search(r"<h3>(.*)<", address)
        data = match.groups()

        if data:
            return data[0]

        return None

    def parse(self, response):
        results = response.json()
        results = results["results"]
        for data in results:
            properties = {
                "city": data["district"],
                "ref": data["id"],
                "phone": data["telephone"].strip(),
                "lon": data["longitude"],
                "lat": data["latitude"],
                "name": data["name"],
            }

            address = self.parse_address(data["addresses"][0])
            if address:
                properties["addr_full"] = address

            opening_hours = self.store_hours(data)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
