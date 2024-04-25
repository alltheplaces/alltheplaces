import re
from datetime import datetime

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class FairwayMarketUSSpider(scrapy.Spider):
    name = "fairway_market_us"
    item_attributes = {"brand": "Fairway Market", "brand_wikidata": "Q5430910"}
    allowed_domains = ["fairwaymarket.com"]
    start_urls = [
        "https://www.fairwaymarket.com/api/models/stores?posts_per_page=40",
    ]
    requires_proxy = True  # Cloudflare geoblocking in use

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if hour["name"] not in DAYS_NAME:
                pass
            else:
                d = hour["name"]
                day = DAYS_NAME[d]
                open = hour["open_time"] + hour["open_period"].upper()
                open_time = datetime.strptime(open, "%I:%M%p").strftime("%H:%M")
                close = hour["close_time"] + hour["close_period"].upper()
                close_time = datetime.strptime(close, "%I:%M%p").strftime("%H:%M")

                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores["data"]:
            addr = re.search(r"^(.*?),", store["location"]["address"]).groups()[0]
            try:
                city = re.search(r",\s(.*?),", store["location"]["address"]).groups()[0]
            except:
                city = re.search(r"(Avenue|Parkway)(.*?),", store["location"]["address"]).groups()[1].strip()
                addr = re.search(r"^(.*)(Avenue|Parkway)", store["location"]["address"]).group(0)

            state = re.search(r"[A-Z]{2}", store["location"]["address"])[0]
            postal = re.search(r"[0-9]{5}", store["location"]["address"])[0]

            properties = {
                "ref": store["ID"],
                "name": store["name"],
                "addr_full": addr,
                "city": city,
                "state": state,
                "postcode": postal,
                "country": "US",
                "lat": store["location"]["lat"],
                "lon": store["location"]["lng"],
                "phone": store["main_phone"],
                "website": store["guid"],
            }

            h = self.parse_hours(store["hours"])
            if h:
                properties["opening_hours"] = h

            yield Feature(**properties)
