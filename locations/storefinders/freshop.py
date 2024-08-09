from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# To use this store finder, specify the brand/application key using
# the "app_key" attribute of this class. You may need to define a
# parse_item function to extract additional location data and to
# make corrections to automatically extracted location data.


class FreshopSpider(Spider):
    dataset_attributes = {"source": "api", "api": "freshop.com"}
    app_key: str = ""
    location_type_ids: list[str] = ["1567647"]

    def start_requests(self):
        yield JsonRequest(url=f"https://api.freshop.com/1/stores?app_key={self.app_key}")

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            if location.get("type_id") not in self.location_type_ids or not location.get("has_address"):
                continue
            if "COMING SOON" in location.get("hours_md", "").upper():
                continue

            item = DictParser.parse(location)

            if location.get("store_number"):
                item["ref"] = location["store_number"]

            item["street_address"] = ", ".join(
                filter(None, [location.get("address_1"), location.get("address_2"), location.get("address_3")])
            )

            if location.get("hours_md"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["hours_md"])

            if "has_delivery" in location.keys():
                apply_yes_no(Extras.DELIVERY, item, location.get("has_delivery"), False)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
