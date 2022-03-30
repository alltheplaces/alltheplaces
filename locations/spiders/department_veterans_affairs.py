# -*- coding: utf-8 -*-
import scrapy
import datetime
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class VeteransAffairsSpider(scrapy.Spider):
    name = "department_veterans_affairs"
    item_attributes = {"brand": "Department Veterans Affairs"}
    allowed_domains = ["api.va.gov"]

    def start_requests(self):

        for i in range(1, 117):
            URL = (
                "https://api.va.gov/v0/facilities/va?address=United%%20States&bbox[]=-180&bbox[]=90&bbox[]=180&bbox[]=-90&type=all&page=%s"
                % i
            )
            yield scrapy.Request(URL, callback=self.parse_info)

    def store_hours(self, store_hours):
        o = OpeningHours()

        for day in (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ):
            hours = store_hours.get(day)
            d = day[:2]
            d = d.title()

            if not hours:
                continue

            try:
                m = re.match(
                    r"((1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm]))-((1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm]))",
                    hours,
                )
                try:
                    open = datetime.datetime.strptime(m.group(1), "%I:%M%p").strftime(
                        "%H:%M"
                    )
                    close = datetime.datetime.strptime(m.group(5), "%I:%M%p").strftime(
                        "%H:%M"
                    )
                except:
                    continue

                o.add_range(d, open_time=open, close_time=close, time_format="%H:%M")
            except AttributeError:
                continue

        return o.as_opening_hours()

    def parse_info(self, response):
        data = response.json()

        data = data["data"]

        for row in data:
            place_info = row["attributes"]

            try:
                addr = place_info["address"]["physical"]["address_1"]
            except:
                addr = place_info["address"]["mailing"]["address_1"]

            properties = {
                "ref": row["id"],
                "name": place_info["name"],
                "lat": place_info["lat"],
                "lon": place_info["long"],
                "addr_full": addr,
                "city": place_info["address"]["physical"]["city"],
                "state": place_info["address"]["physical"]["state"],
                "country": "US",
                "postcode": place_info["address"]["physical"]["zip"],
                "website": place_info["website"],
                "phone": place_info["phone"]["main"],
                "extras": {"type": place_info["facility_type"]},
            }

            hours = place_info.get("hours")
            opening_hours = self.store_hours(hours)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
