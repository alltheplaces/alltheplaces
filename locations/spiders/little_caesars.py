import json

import scrapy

from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT

DAY_MAPPING = {
    "SUN": "Su",
    "MON": "Mo",
    "TUE": "Tu",
    "WED": "We",
    "THU": "Th",
    "FRI": "Fr",
    "SAT": "Sa",
}


class LittleCaesarsSpider(scrapy.Spider):
    name = "little_caesars"
    item_attributes = {
        "brand": "Little Caesars",
        "brand_wikidata": "Q1393809",
        "country": "US",
    }
    allowed_domains = ["littlecaesars.com"]
    download_delay = 0.1
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        for record in postal_regions("US"):
            url = "https://api.cloud.littlecaesars.com/bff/api/stores?zip=" + record["postal_region"]
            yield scrapy.http.Request(url, self.parse, method="GET")

    def parse(self, response):
        body = response.text
        if not body:
            return

        result = json.loads(body)
        stores = result.get("stores")

        for store in stores:
            store_id = store.get("storeId")
            if not store_id:
                continue

            # We already have some details about each store returned from the search
            # in our current response, but a superset of these details are available
            # through another API.
            yield scrapy.http.Request(
                url=f"https://api.cloud.littlecaesars.com/bff/api/stores/{store_id}",
                method="GET",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        body = response.text
        if not body:
            return

        result = json.loads(body)
        store = result.get("store")
        if not store:
            return

        address = store.get("address")
        if not address:
            return

        properties = {
            # 'siteId' appears to be the publicly facing store number.  I would prefer to use it, but
            # it comes back as null for some stores.  'id' also appears in the data, reliably.
            # So use it instead.
            "ref": store.get("locationNumber"),
            "street_address": merge_address_lines([address.get("street"), address.get("street2")]),
            "city": address.get("city"),
            "state": address.get("state"),
            "postcode": address.get("zip"),
            "phone": store.get("phone"),
            "website": response.url,
            "lon": store.get("longitude"),
            "lat": store.get("latitude"),
        }

        opening_hours = self.add_hours(result.get("orderingHours"))
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield Feature(**properties)

    def add_hours(self, ordering_hours):
        opening_hours = OpeningHours()

        for o in ordering_hours:
            try:
                opening_hours.add_range(
                    DAY_MAPPING[o["dayName"]],
                    f"{o['hourOpen']}:{o['minuteOpen']}",
                    f"{o['hourClose']}:{o['minuteClose']}",
                )
            except (KeyError, ValueError):
                # In rare cases, we've seen the day name is missing from the data.
                # If we hit any errors at all, don't return opening hours, even if
                # we were able to get opening hours for different day names.  Otherwise,
                # we may give the false impression the location is closed on certain days.
                return

        return opening_hours.as_opening_hours()
