# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class FoodLionSpider(scrapy.Spider):
    download_delay = 3
    name = "foodlion"
    item_attributes = {"brand": "Food Lion", "brand_wikidata": "Q1435950"}
    allowed_domains = ["www.foodlion.com"]
    start_urls = ("https://www.foodlion.com/stores/",)

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def start_requests(self):
        states = ["GA", "SC", "NC", "MD", "TN", "VA"]
        template = "https://www.foodlion.com/bin/foodlion/search/storelocator.json?zip={state}&distance=1000&onlyPharmacyEnabledStores=false"

        headers = {
            "Accept": "application/json",
        }

        for state in states:
            yield scrapy.http.FormRequest(
                url=template.format(state=state),
                method="GET",
                headers=headers,
                callback=self.parse,
            )

    def parse(self, response):
        jsonresponse = response.json()
        stores = json.loads(jsonresponse["result"])
        for store in stores:
            properties = {
                "name": store["title"],
                "ref": store["storeId"],
                "addr_full": store["address"].strip(),
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": "US",
                "phone": store["phoneNumber"],
                "lat": float(store["lat"]),
                "lon": float(store["lon"]),
                "website": "https://www.foodlion.com" + store["href"],
            }

            hours = store["hours"]

            if hours:
                properties["opening_hours"] = self.process_hours(hours)

            yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        day_groups = []
        for line in hours:
            this_day_group = dict()
            if ": " not in line:
                continue
            (front, rest) = line.split(": ")
            days = front.split("-")
            if days:
                this_day_group["from_day"] = days[0][:2]
                this_day_group["to_day"] = days[0][:2]
            if len(days) == 2:
                this_day_group["to_day"] = days[1][:2]

            if rest == "Closed":
                continue
            elif rest:
                match = re.search(r"^(\d+):(\d+) (am|pm)-(\d+):(\d+) (am|pm)$", rest)
                if match:
                    (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()
                    if f_ampm == "pm":
                        f_hr = int(f_hr) + 12
                    if t_ampm == "pm":
                        t_hr = int(t_hr) + 12

                    this_day_group["hours"] = "{:02d}:{:02d}-{:02d}:{:02d}".format(
                        int(f_hr),
                        int(f_min),
                        int(t_hr),
                        int(t_min),
                    )
                elif rest == "Open 24 Hours":
                    this_day_group["hours"] = "24/7"

                day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] == "24/7":
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
