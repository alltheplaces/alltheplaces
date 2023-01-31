import re

import scrapy

from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class KruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    allowed_domains = ["kruidvat.nl"]
    start_urls = ["https://www.kruidvat.nl/api/v2/kvn/stores?lang=nl&radius=100000&pageSize=10000&fields=FULL"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/json",
        }
    }

    def parse(self, response):
        for store in response.json().get("stores"):
            oh = OpeningHours()
            for day in store.get("openingHours", {}).get("weekDayOpeningList"):
                oh.add_range(
                    day=sanitise_day(day.get("weekDay")[:2], DAYS_NL),
                    open_time=day.get("openingTime", {}).get("formattedHour"),
                    close_time=day.get("closingTime", {}).get("formattedHour"),
                )

            properties = {
                "name": store.get("name"),
                "ref": store.get("address", {}).get("id"),
                "addr_full": store.get("address", {}).get("formattedAddress"),
                "street_address": store.get("address", {}).get("line1"),
                "country": store.get("address", {}).get("country").get("isocode"),
                "city": store.get("address").get("town"),
                "state": store["address"].get("province"),
                "postcode": store.get("address", {}).get("postalCode"),
                "lat": store.get("geoPoint", {}).get("latitude"),
                "lon": store.get("geoPoint", {}).get("longitude"),
                "website": "https://www.kruidvat.nl{}".format(re.sub(r"\?.+", "", store.get("url"))),
                "opening_hours": oh.as_opening_hours(),
            }

            yield Feature(**properties)
