import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

SERVICE_VALUES = {"Yes": True, "No": False, "NR": None}
TIME_PATTERN = re.compile(r"\d{2}:\d{2}")


class CitgoSpider(scrapy.Spider):
    name = "citgo"
    item_attributes = {"brand": "Citgo", "brand_wikidata": "Q2974437"}
    allowed_domains = ["citgo.com"]

    start_urls = ["https://citgo.com/locator/store-locators/store-locator"]

    def parse(self, response):
        if response.request.method == "GET":
            # We first need to fetch the page normally and extract some required tokens from the form
            yield scrapy.FormRequest(
                self.start_urls[0],
                method="POST",
                formdata={
                    "__CMSCsrfToken": response.css("#__CMSCsrfToken::attr(value)").get(),
                    "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").get(),
                    "__CALLBACKID": "p$lt$WebPartZone3$PageContent$pageplaceholder$p$lt$WebPartZone3$Widgets$StoreLocator",
                    "__CALLBACKPARAM": "66952|10000",
                },
            )
        else:
            # The first character of the response is `s`; after that it's JSON
            result = json.loads(response.text[1:])

            for location in result["Locations"]:
                opening_hours = OpeningHours()
                services = location["services"]

                for hours_key in ["sun", "mon", "tues", "wed", "thurs", "fri", "sat"]:
                    open_time = location[f"hrs{hours_key}start"]
                    close_time = location[f"hrs{hours_key}start"]

                    if not (TIME_PATTERN.match(open_time) and TIME_PATTERN.match(close_time)):
                        continue

                    if int(open_time[0:2]) >= 24:
                        open_time = f"{(int(open_time[0:2]) - 24):02d}{open_time[2:]}"

                    if int(close_time[0:2]) >= 24:
                        close_time = f"{(int(close_time[0:2]) - 24):02d}{close_time[2:]}"

                    opening_hours.add_range(
                        day=hours_key[:2].capitalize(),
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

                yield Feature(
                    ref=location["number"],
                    lon=location["longitude"],
                    lat=location["latitude"],
                    name=location["name"],
                    addr_full=location["address"],
                    city=location["city"],
                    state=location["state"],
                    postcode=location["zip"],
                    country=location["country"],
                    phone=location["phone"],
                    opening_hours=opening_hours.as_opening_hours(),
                    extras={
                        "amenity:fuel": True,
                        "atm": SERVICE_VALUES.get(services["atm"]),
                        "car_wash": SERVICE_VALUES.get(services["carwash"]),
                        "fuel:diesel": SERVICE_VALUES.get(services["diesel"]),
                        "hgv": SERVICE_VALUES.get(services["truckstop"]),
                        "wheelchair": SERVICE_VALUES.get(services["handicapaccess"]),
                        "shop": "convenience" if SERVICE_VALUES.get(services["cstore"]) else None,
                    },
                )
