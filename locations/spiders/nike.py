import datetime

import scrapy
import re

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class NikeSpider(scrapy.Spider):
    name = "nike"
    item_attributes = {"brand": "Nike", "brand_wikidata": "Q483915"}
    allowed_domains = ["storeviews-cdn.risedomain-prod.nikecloud.com"]
    download_delay = 0.3

    def start_requests(self):
        url = "https://storeviews-cdn.risedomain-prod.nikecloud.com/store-locations-static.json"

        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        store = response.json()
        all_stores = store["stores"]

        for store in all_stores:
            store = all_stores.get(store)
            addresses = store.get("address")
            coords = store.get("coordinates")

            addr_1 = addresses.get("address_1")
            addr_2 = addresses.get("address_2")
            addr_3 = addresses.get("address_3")
            days = (
                store.get("operationalDetails")
                .get("hoursOfOperation")
                .get("regularHours")
            )
            opening_hours = OpeningHours()
            for day in days:
                if len(days.get(day)) > 0:

                    oh = days.get(day)[0]
                    opening = oh.get("startTime")
                    closing = oh.get("duration")

                    closing_h = (
                        closing.split("H")[0].replace("PT", "")
                        if "H" in closing
                        else "0"
                    )
                    closing_m = (
                        closing[len(closing) - 3 :].replace("M", "")
                        if "M" in closing
                        else "0"
                    )

                    start = opening.split(":")
                    closing_time = str(
                        datetime.timedelta(hours=int(start[0]), minutes=int(start[1]))
                        + datetime.timedelta(
                            hours=int(closing_h), minutes=int(closing_m)
                        )
                    )
                    if "day" in closing_time:
                        closing_time = "00:00"
                    else:
                        split_closing_time = closing_time.split(":")
                        closing_time = "".join(
                            split_closing_time[0] + ":" + split_closing_time[1]
                        )

                    opening_hours.add_range(day[0:2].title(), opening, closing_time)

            properties = {
                "name": store.get("name"),
                "ref": store.get("id"),
                "addr_full": re.sub(
                    " +", " ", " ".join(filter(None, [addr_1, addr_2, addr_3])).strip()
                ),
                "city": addresses.get("city"),
                "state": addresses.get("state"),
                "postcode": store.get("postalCode"),
                "country": addresses.get("country"),
                "phone": store.get("phone"),
                "website": response.url,
                "opening_hours": opening_hours.as_opening_hours(),
                "lat": coords.get("latitude"),
                "lon": coords.get("longitude"),
                "extras": {
                    "store_type": store.get("facilityType"),
                },
            }

            yield GeojsonPointItem(**properties)
