import json
import re

import scrapy

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class IntersportNLSpider(scrapy.Spider):
    name = "intersport_nl"
    start_urls = ["https://www.intersport.nl/stores"]

    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}

    def parse(self, response, **kwargs):
        pattern = r"var\s+storesJson\s*=\s*(\[.*?\]);"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            oh = OpeningHours()
            for day, hours in store.get("storeHours", {}).items():
                capitalized_day = day.capitalize()
                if day.capitalize() not in DAYS_EN.keys():
                    continue
                oh.add_range(
                    day=DAYS_EN.get(capitalized_day),
                    open_time=hours.get("fromFirst")[:5],
                    close_time=hours.get("toFirst")[:5],
                    time_format="%H:%M",
                )
            yield Feature(
                {
                    "ref": store.get("storeID"),
                    "name": store.get("name"),
                    "street_address": " ".join(
                        filter(None, [store.get("houseNr"), store.get("houseNrAddition"), store.get("address2")])
                    ),
                    "housenumber": " ".join([store.get("houseNr"), store.get("houseNrAddition")]),
                    "street": store.get("address1"),
                    "phone": store.get("phone"),
                    "email": store.get("email"),
                    "postcode": store.get("postalCode"),
                    "city": store.get("city"),
                    "state": store.get("state"),
                    "country": store.get("countryCode"),
                    "website": store.get("link"),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "opening_hours": oh,
                }
            )
