import json
import re
from datetime import datetime

import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

DAY_MAPPING = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class BjsWholesaleSpider(scrapy.Spider):
    name = "bjs_wholesale"
    item_attributes = {
        "brand": "BJ's Wholesale",
        "brand_wikidata": "Q4835754",
        "extras": Categories.SHOP_WHOLESALE.value,
    }
    allowed_domains = ["bjs.com"]
    start_urls = [
        "https://api.bjs.com/digital/live/apis/v1.0/clublocatorpage/statetowns/10201",
    ]
    headers = {"Content-Type": "application/json"}

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        if hours:
            hours = hours[0].get("value").split("<br>") or []
            for hour in hours:
                try:
                    day, open_time, close_time = re.search(r"(.*?):\s(.*?)\s-\s(.*?)$", hour).groups()
                except AttributeError:  # closed
                    continue
                open_time = (
                    datetime.strptime(open_time, "%I:%M %p")
                    if ":" in open_time
                    else datetime.strptime(open_time, "%I %p")
                ).strftime("%H:%M")
                close_time = (
                    datetime.strptime(close_time, "%I:%M %p")
                    if ":" in close_time
                    else datetime.strptime(close_time, "%I %p")
                ).strftime("%H:%M")

                if "-" in day:
                    start_day, end_day = day.split("-")
                    start_day = start_day.strip()
                    end_day = end_day.strip()
                    for d in DAY_MAPPING[DAY_MAPPING.index(start_day[:2]) : DAY_MAPPING.index(end_day[:2]) + 1]:
                        opening_hours.add_range(
                            day=d,
                            open_time=open_time,
                            close_time=close_time,
                            time_format="%H:%M",
                        )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        data = response.json()["Stores"]["PhysicalStore"][0]

        properties = {
            "name": data["Description"][0]["displayStoreName"],
            "ref": data["storeName"],
            "street_address": clean_address(data["addressLine"]),
            "city": data["city"].strip(),
            "state": data["stateOrProvinceName"].strip(),
            "postcode": data["postalCode"].strip(),
            "country": data["country"].strip(),
            "phone": data.get("telephone1", "").strip(),
            "website": "https://www.bjs.com/mapDetail;city={}".format(data["storeName"]),
            "lat": float(data["latitude"]),
            "lon": float(data["longitude"]),
        }

        hours = self.parse_hours([attr for attr in data["Attribute"] if attr["name"] == "Hours of Operation"])
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse(self, response):
        data = response.json()

        for state in data["clubLocatorStateTownList"]:
            for town in state["Towns"]:
                code, _ = town.split("|")
                payload = {
                    "Town": code,
                    "latitude": "",
                    "longitude": "",
                    "radius": "",
                    "zipCode": "",
                }
                yield scrapy.FormRequest(
                    "https://api.bjs.com/digital/live/api/v1.0/club/search/10201",
                    method="POST",
                    body=json.dumps(payload),
                    headers=self.headers,
                    callback=self.parse_store,
                )
