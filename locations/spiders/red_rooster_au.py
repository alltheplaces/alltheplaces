import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RedRoosterAUSpider(Spider):
    name = "red_rooster_au"
    item_attributes = {"brand": "Red Rooster", "brand_wikidata": "Q376466"}
    # robots.txt returns a HTTP 403 error which confuses Scrapy
    custom_settings = {"ROBOTSTXT_OBEY": False}
    api_url = "https://api.redrooster.com.au/olo/store/getall"
    api_key = "WDnfnaRMYSUJXkDp3SLh5VwUXe9jjXV7EBjYQNW0"

    def start_requests(self):
        yield JsonRequest(url=self.api_url, headers={"x-api-key": self.api_key})

    def parse(self, response):
        for location in response.json()["store"]:
            item = DictParser.parse(location)
            if (
                location["attributes"]["isStorePermanentclosed"]
                or not location["attributes"]["isEnabled"]
                or location["attributes"]["storeName"] == "Red Rooster Lab Test Store"
            ):
                continue

            item["name"] = location["attributes"]["storeName"]
            item["phone"] = location["attributes"].get("storePhone")
            item["email"] = location["attributes"].get("storeEmail")

            if "urlPath" in location["relationships"].keys():
                item["website"] = (
                    "https://redrooster.com.au/locations/"
                    + location["relationships"]["urlPath"]["data"]["attributes"]["path"]
                    + "/"
                )

            if "storeAddress" in location["relationships"].keys():
                address_fields = location["relationships"]["storeAddress"]["data"]["attributes"]["addressComponents"]
                item["lat"] = address_fields["latitude"]["value"]
                item["lon"] = address_fields["longitude"]["value"]
                item["street_address"] = re.sub(r"\s+", " ", address_fields["streetName"]["value"])
                item["city"] = address_fields["suburb"]["value"]
                item["postcode"] = address_fields["postcode"]["value"]
                item["state"] = address_fields["state"]["value"]

            item["opening_hours"] = OpeningHours()
            for trading_day in location["attributes"]["tradingHours"]:
                for hours_range_index, hours_range in enumerate(trading_day["hours"]):
                    open_time = trading_day["hours"][hours_range_index]["openTime"]
                    close_time = trading_day["hours"][hours_range_index]["closeTime"]
                    if "Invalid date" in open_time or "Invalid date" in close_time:
                        continue
                    item["opening_hours"].add_range(trading_day["dayOfWeek"], open_time, close_time, "%H:%M:%S")

            if "payment" in location["relationships"].keys():
                payment_methods = location["relationships"]["payment"]["data"]["attributes"].keys()
                apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "card" in payment_methods, False)
                apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "card" in payment_methods, False)
                apply_yes_no(PaymentMethods.CASH, item, "cash" in payment_methods, False)
                apply_yes_no(PaymentMethods.APPLE_PAY, item, "apple_pay" in payment_methods, False)
                apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "google_pay" in payment_methods, False)

            if "amenities" in location["relationships"].keys():
                amenities = [
                    amenity
                    for amenity, available in location["relationships"]["amenities"]["data"]["attributes"].items()
                    if available
                ]
                apply_yes_no(Extras.WIFI, item, "haveWifi" in amenities, False)
                apply_yes_no(Extras.TOILETS, item, "haveToilet" in amenities, False)

            if "collection" in location["relationships"].keys():
                apply_yes_no(
                    Extras.DRIVE_THROUGH,
                    item,
                    location["relationships"]["collection"]["data"]["attributes"]["pickupTypes"]["driveThru"],
                    False,
                )
                apply_yes_no(
                    Extras.TAKEAWAY,
                    item,
                    location["relationships"]["collection"]["data"]["attributes"]["pickupTypes"]["instore"],
                    False,
                )

            if "availability" in location["relationships"].keys():
                apply_yes_no(
                    Extras.DELIVERY,
                    item,
                    location["relationships"]["availability"]["data"]["attributes"]["web"]["delivery"]["isEnabled"],
                    False,
                )

            yield item
