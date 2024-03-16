import datetime
import re

import scrapy
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DepartmentVeteransAffairsSpider(scrapy.Spider):
    name = "department_veterans_affairs"
    item_attributes = {"brand": "Department Veterans Affairs", "brand_wikidata": "Q592576"}
    allowed_domains = ["api.va.gov"]

    def start_requests(self):
        yield JsonRequest(
            "https://api.va.gov/facilities_api/v1/va?bbox[]=-180&bbox[]=90&bbox[]=180&bbox[]=-90&per_page=50",
            callback=self.parse_info,
        )

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
                    open = datetime.datetime.strptime(m.group(1), "%I:%M%p").strftime("%H:%M")
                    close = datetime.datetime.strptime(m.group(5), "%I:%M%p").strftime("%H:%M")
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

            addr = place_info["address"]["physical"]
            if not addr:
                addr = place_info["address"]["mailing"]

            properties = {
                "ref": row["id"],
                "name": place_info["name"],
                "lat": place_info["lat"],
                "lon": place_info["long"],
                "street_address": merge_address_lines(
                    [addr.get("address1"), addr.get("address2"), addr.get("address3")]
                ),
                "city": addr.get("city"),
                "state": addr.get("state"),
                "country": "US",
                "postcode": addr.get("zip"),
                "website": place_info["website"],
                "phone": place_info["phone"]["main"],
                "extras": {"type": row["type"]},
            }

            hours = place_info.get("hours")
            opening_hours = self.store_hours(hours)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield Feature(**properties)

        if next_url := response.json()["links"]["next"]:
            yield JsonRequest(next_url, callback=self.parse_info)
