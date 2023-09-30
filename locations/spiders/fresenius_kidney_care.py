import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class FreseniusKidneyCareSpider(scrapy.Spider):
    name = "freseniuskidneycare"
    item_attributes = {"brand": "Fresenius Kidney Care", "brand_wikidata": "Q650259"}
    allowed_domains = ["www.freseniuskidneycare.com"]
    download_delay = 0.2
    start_urls = ("https://www.freseniuskidneycare.com/dialysis-centers#locator-search",)

    def start_requests(self):
        base_url = "https://www.freseniuskidneycare.com/dialysis-centers?lat={lat}&lng={lng}&radius=100&page=1"

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for group in hours:
            days, open_time, close_time = re.search(r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group).groups()
            days = days.split(",")
            for day in days:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        try:
            extracted_script = response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()

            if extracted_script is None:
                pass
            else:
                json_data = json.loads(extracted_script)
                try:
                    data = json_data[0]

                    properties = {
                        "name": data["name"],
                        "ref": data["branchCode"],
                        "street_address": data["address"]["streetAddress"],
                        "city": data["address"]["addressLocality"],
                        "state": data["address"]["addressRegion"],
                        "postcode": data["address"]["postalCode"],
                        "phone": data.get("telephone"),
                        "website": data.get("url") or response.url,
                        "lat": float(data["geo"]["latitude"]),
                        "lon": float(data["geo"]["longitude"]),
                    }

                    hours = self.parse_hours(data["openingHours"])
                    if hours is None:
                        pass
                    else:
                        properties["opening_hours"] = hours
                    yield Feature(**properties)
                except:
                    properties = {
                        "name": json_data["name"],
                        "ref": json_data["branchCode"],
                        "street_address": json_data["address"]["streetAddress"],
                        "city": json_data["address"]["addressLocality"],
                        "state": json_data["address"]["addressRegion"],
                        "postcode": json_data["address"]["postalCode"],
                        "phone": json_data.get("telephone"),
                        "website": json_data.get("url") or response.url,
                        "lat": float(json_data["geo"]["latitude"]),
                        "lon": float(json_data["geo"]["longitude"]),
                    }

                    hours = self.parse_hours(json_data["openingHours"])
                    if hours is None:
                        pass
                    else:
                        properties["opening_hours"] = hours
                    yield Feature(**properties)
                else:
                    pass
        except:
            pass
