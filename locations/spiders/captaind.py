# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

NUMBER_DAY = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class CaptainDSpider(scrapy.Spider):

    name = "captaind"
    item_attributes = {"brand": "Captain D's"}
    allowed_domains = [
        "momentfeed-prod.apigee.net",
    ]

    start_urls = (
        "https://momentfeed-prod.apigee.net/api/llp.json?auth_token=AJXCZOENNNXKHAKZ&country=US&sitemap=true",
    )

    def parse_hours(self, hours):
        "1,1030,2200;2,1030,2200;3,1030,2200;4,1030,2200;5,1030,2300;6,1030,2300;7,1030,2200;"
        opening_hours = OpeningHours()
        if hours:
            days = [day for day in hours.split(";") if day]
            for day in days:
                day, from_hr, to_hr = day.split(",")
                opening_hours.add_range(
                    day=NUMBER_DAY[day],
                    open_time=from_hr,
                    close_time=to_hr,
                    time_format="%H%M",
                )
        return opening_hours.as_opening_hours()

    def parse(self, response):

        stores = response.json()

        for store in stores:
            opening_hours = ""
            if store.get("store_info", "").get("store_hours", ""):
                opening_hours = self.parse_hours(store["store_info"]["store_hours"])

            props = {
                "name": store["store_info"]["brand_name"],
                "ref": store["store_info"]["corporate_id"],
                "addr_full": store["store_info"]["address"],
                "postcode": store["store_info"]["postcode"],
                "state": store["store_info"]["region"],
                "website": store["store_info"]["website"],
                "city": store["store_info"]["locality"],
                "phone": store["store_info"]["phone"],
                "lat": float(store["store_info"]["latitude"]),
                "lon": float(store["store_info"]["longitude"]),
                "opening_hours": opening_hours,
            }

            yield GeojsonPointItem(**props)
