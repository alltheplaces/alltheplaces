import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {1: "Su", 2: "Mo", 3: "Tu", 4: "We", 5: "Th", 6: "Fr", 7: "Sa"}


class GiantEagleSpider(scrapy.Spider):
    name = "giant_eagle"
    item_attributes = {"brand": "Giant Eagle", "brand_wikidata": "Q1522721"}
    allowed_domains = "www.gianteagle.com"
    start_urls = (
        "https://www.gianteagle.com/api/sitecore/locations/getlocationlistvm?q=&orderBy=geo.distance(storeCoordinate,%20geography%27POINT(-97.68194299999999%2030.2737366)%27)%20asc&skip=0",
    )
    items_per_page = 12  # api limit

    def parse_hours(self, hours):
        o = OpeningHours()
        for h in hours:
            day = DAY_MAPPING[h["DayNumber"]]
            open = h["Range"].get("Open")
            close = h["Range"].get("Close")
            if h["IsOpenedAllDay"]:
                open = "0:00"
                close = "23:59"
            elif h["IsClosedAllDay"]:
                continue

            if open and close:
                o.add_range(day=day, open_time=open, close_time=close)
        return o.as_opening_hours()

    def parse_address(self, address):
        return ", ".join(
            filter(
                lambda x: True if x and x != "-" else False,
                [address["address_no"], address["lineOne"], address["lineTwo"]],
            )
        )

    def parse(self, response):
        page_regex = re.compile(r"skip=(\d+)")
        page = int(page_regex.search(response.url).group(1))

        stores = response.json()["Locations"] or []

        for store in stores:
            telephone = None
            if store.get("TelephoneNumbers"):
                for t in store["TelephoneNumbers"]:
                    if t["location"]["Item2"] == "Main":
                        telephone = t["DisplayNumber"]

            properties = dict(
                ref=store["Number"]["Value"],
                name=store["Name"],
                street_address=self.parse_address(store["Address"]),
                lat=store["Address"]["Coordinates"]["Latitude"],
                lon=store["Address"]["Coordinates"]["Longitude"],
                country="US",
                city=store["Address"]["City"],
                state=store["Address"]["State"]["Abbreviation"],
                postcode=store["Address"]["Zip"],
                phone=telephone,
                opening_hours=self.parse_hours(store["HoursOfOperation"]),
                extras={
                    "number": store["Number"]["Value"],
                    "display_name": store["StoreDisplayName"],
                },
            )

            yield Feature(**properties)

        if stores:
            page += self.items_per_page
            yield scrapy.Request(
                url=page_regex.sub("skip={}".format(page), response.url),
                dont_filter=True,
            )
