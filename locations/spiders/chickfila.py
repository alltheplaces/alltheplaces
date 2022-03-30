# -*- coding: utf-8 -*-
import scrapy
import re
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

DAYS_NAME = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}

HEADERS = {"Accept": "application/json"}


class ChickFilASpider(scrapy.Spider):
    name = "chickfila"
    item_attributes = {"brand": "Chick-Fil-A", "brand_wikidata": "Q491516"}
    allowed_domains = ["chick-fil-a.com", "yext-cdn.com"]

    def start_requests(self):
        for state in STATES:
            yield scrapy.Request(
                "https://locator.chick-fil-a.com.yext-cdn.com/search?per=50&per=10&offset=0&q="
                + state,
                headers=HEADERS,
            )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:

            if hour["isClosed"]:
                pass
            else:
                day = DAYS_NAME[hour["day"]]
                open_time = str(hour["intervals"][0]["start"])
                close_time = str(hour["intervals"][0]["end"])
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        stores = stores["response"]["entities"]

        if stores:

            for store in stores:

                properties = {
                    "name": store["profile"]["c_locationName"],
                    "addr_full": " ".join(
                        [
                            store["profile"]["address"]["line1"],
                            store.get("line2", ""),
                            store.get("line3", ""),
                        ]
                    ).strip(),
                    "city": store["profile"]["address"]["city"],
                    "state": store["profile"]["address"]["region"],
                    "postcode": store["profile"]["address"]["postalCode"],
                    "phone": store["profile"].get("c_preferredPhone"),
                    "website": store["profile"]["websiteUrl"],
                    "ref": store["distance"]["id"],
                    "lat": store["profile"]["displayCoordinate"]["lat"],
                    "lon": store["profile"]["displayCoordinate"]["long"],
                }
                opening_hours = self.parse_hours(
                    store["profile"]["hours"]["normalHours"]
                )
                properties["opening_hours"] = opening_hours

                yield GeojsonPointItem(**properties)

            offset = int(re.search(r"offset=(\d+)", response.url).groups()[0])
            url = response.urljoin(
                response.url.replace(
                    "offset={}".format(offset), "offset={}".format(offset + 50)
                )
            )
            yield scrapy.Request(url, headers=HEADERS)
