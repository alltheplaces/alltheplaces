from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class RedRoosterAUSpider(Spider):
    name = "red_rooster_au"
    item_attributes = {"brand": "Red Rooster", "brand_wikidata": "Q376466", "extras": Categories.FAST_FOOD.value}
    start_urls = ["https://content-acl.redrooster.com.au/all_stores.json"]
    allowed_domains = ["content-acl.redrooster.com.au"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            if location["attributes"]["isEnabledForTrading"] is not True:
                # Ignore closed locations.
                continue

            # Note: unit, floor and streetNumber fields are present but never
            # used. These fields can be ignored.
            address_fields = location["relationships"]["storeAddress"]["data"]["attributes"]["addressComponents"]

            properties = {
                "ref": location["id"],
                "branch": location["attributes"]["storeName"].removeprefix("Red Rooster "),
                "lat": address_fields.get("latitude", {}).get("value"),
                "lon": address_fields.get("longitude", {}).get("value"),
                "street_address": address_fields.get("streetName", {}).get("value"),
                "city": address_fields.get("suburb", {}).get("value"),
                "state": address_fields.get("state", {}).get("value"),
                "postcode": address_fields.get("postcode", {}).get("value"),
                "email": location["attributes"].get("storeEmail"),
                "phone": location["attributes"].get("storePhone"),
                "website": "https://www.redrooster.com.au/locations/"
                + location["relationships"]["slug"]["data"]["attributes"]["slug"],
            }

            properties["opening_hours"] = OpeningHours()
            for day_hours in location["relationships"]["collection"]["data"]["attributes"]["collectionTimes"]:
                for time_period in day_hours["collectionTimePeriods"]:
                    properties["opening_hours"].add_range(
                        day_hours["dayOfWeek"], time_period["openTime"], time_period["closeTime"], "%H:%M:%S"
                    )

            apply_yes_no(
                Extras.DRIVE_THROUGH,
                properties,
                location["relationships"]["collection"]["data"]["attributes"]["pickupTypes"]["driveThru"],
                False,
            )
            apply_yes_no(Extras.DELIVERY, properties, location["attributes"]["isDeliveryEnabled"], False)
            apply_yes_no(
                Extras.WIFI, properties, location["relationships"]["amenities"]["data"]["attributes"]["haveWifi"], False
            )
            apply_yes_no(
                Extras.TOILETS,
                properties,
                location["relationships"]["amenities"]["data"]["attributes"]["haveToilet"],
                False,
            )

            yield Feature(**properties)
