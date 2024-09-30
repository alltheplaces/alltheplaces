from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

# Documentation for the Kibo Commerce Storefront Location API is available at
# https://apidocs.kibocommerce.com/?spec=location_storefront#get-/commerce/storefront/locationUsageTypes/DL/locations
#
# To use this spider, specify a single start URL which is the location of the store's API path of:
# /commerce/storefront/locationUsageTypes/DL/locations


class KiboSpider(Spider, AutomaticSpiderGenerator):
    page_size: int = 1000
    api_filter: str = None
    detection_rules = [
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/api\/commerce\/storefront\/locationUsageTypes\/SP\/locations)(?:\?|\/|$)"
        )
    ]

    def start_requests(self):
        if self.api_filter:
            yield JsonRequest(url=f"{self.start_urls[0]}?pageSize={self.page_size}&filter={self.api_filter}")
        else:
            yield JsonRequest(url=f"{self.start_urls[0]}?pageSize={self.page_size}")

    def parse(self, response: Response):
        for location in response.json()["items"]:
            self.pre_process_data(location)
            item = DictParser.parse(location)

            item["ref"] = location["code"]
            item["city"] = location["address"]["cityOrTown"]
            item["state"] = location["address"]["stateOrProvince"]
            item["postcode"] = location["address"]["postalOrZipCode"]
            if "email" in location["shippingOriginContact"]:
                item["email"] = location["shippingOriginContact"]["email"]
            if not item["phone"] and "phoneNumber" in location["shippingOriginContact"]:
                item["phone"] = location["shippingOriginContact"]["phoneNumber"]

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day in DAYS_FULL:
                hours_for_day = location["regularHours"][day.lower()]
                if hours_for_day["isClosed"]:
                    continue
                if hours_for_day.get("openTime") and hours_for_day.get("closeTime"):
                    open_time = hours_for_day["openTime"]
                    close_time = hours_for_day["closeTime"]
                    hours_string = f"{hours_string} {day}: {open_time} - {close_time}"
                elif hours_label := hours_for_day.get("label"):
                    hours_string = f"{hours_string} {day}: {hours_label}"
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield from self.parse_item(item, location) or []

            self.page_size = response.json()["pageSize"]
            locations_remaining = response.json()["totalCount"] - (response.json()["startIndex"] + self.page_size)
            if locations_remaining > 0:
                next_start_index = response.json()["startIndex"] + self.page_size
                yield JsonRequest(url=f"{self.start_urls[0]}?pageSize={self.page_size}&startIndex={next_start_index}")

    def parse_item(self, item: Feature, location: dict):
        yield item

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""
