# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class CarinosSpider(scrapy.Spider):

    name = "carinos"
    item_attributes = {"brand": "Carino's Italian"}
    allowed_domains = ["www.carinos.com"]
    start_urls = ("http://www.carinos.com/Location/Maps?locationType=2",)

    def store_hours(self, store_hours):

        store_hours = store_hours.replace("Full menu available from", "")

        m = re.search(r"(\r\n)\d", store_hours)
        if m:
            store_hours = store_hours.replace(m.group(1), " ")
        store_hours = store_hours.replace("\r\n", ",")
        m = re.search(r"(,,)\D", store_hours)
        if m:
            store_hours = store_hours.replace(m.group(1), ",")
        m = re.search(r"(\sand\s)", store_hours)
        if m:
            store_hours = store_hours.replace(m.group(1), ",")

        m = re.search(r"(,,)\d", store_hours)
        if m:
            store_hours = store_hours.replace(m.group(1), " ")
        m = re.search(r"(<br>)", store_hours)
        if m:
            store_hours = store_hours.replace(m.group(1), " ")

        store_hours = (
            store_hours.replace("Monday", "Mo")
            .replace("Tuesday", "Tu")
            .replace("Wednesday", "We")
            .replace("Thursday", "Th")
            .replace("Friday", "Fr")
            .replace("Saturday", "Sa")
            .replace("Sunday", "Su")
        )

        for i in range(0, 8):
            m = re.search(r"([0-9]{1,2})(:[0-9]0PM)", store_hours)
            if m:
                h = m.group(1)
                new_h = int(h) + 12
                store_hours = store_hours.replace(m.group(0), str(new_h) + ":00")

            m = re.search(r"([0-9]{1,2})(:[0-9]0AM)", store_hours)
            if m:
                h = m.group(1)
                new_h = int(h)
                if h == 12:
                    new_h -= 12
                store_hours = store_hours.replace(m.group(0), str(new_h) + ":00")
        for i in range(0, 8):
            m = re.search(r"([0-9]{1,2})(PM)", store_hours)
            if m:
                h = m.group(1)
                new_h = int(h) + 12
                store_hours = store_hours.replace(m.group(0), str(new_h) + ":00")

            m = re.search(r"([0-9]{1,2})(AM)", store_hours)
            if m:
                h = m.group(1)
                new_h = int(h)
                if h == 12:
                    new_h -= 12
                store_hours = store_hours.replace(m.group(0), str(new_h) + ":00")
        store_hours = store_hours.replace("\u2013", "-")
        store_hours = store_hours.replace("<p>", "")

        return store_hours

    def parse(self, response):
        results = response.json()

        for data in results:
            properties = {
                "ref": data["Location"]["LocationID"],
                "name": data["Location"]["LocationName"],
                "lat": data["Location"]["Latitude"],
                "lon": data["Location"]["Longitude"],
                "addr_full": data["Location"]["Address1"],
                "city": data["Location"]["City"],
                "country": data["Location"]["Country"],
                "state": data["Location"]["State"],
                "postcode": data["Location"]["Zip"],
                "phone": data["Location"]["Phone1"],
                "opening_hours": self.store_hours(data["Location"]["Hours"]),
                "website": data["Location"]["URL"],
            }

            yield GeojsonPointItem(**properties)
