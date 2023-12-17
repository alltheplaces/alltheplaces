from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

# Documentation for the Kibo Commerce Storefront Location API is available at
# https://apidocs.kibocommerce.com/?spec=location_storefront#get-/commerce/storefront/locationUsageTypes/DL/locations
#
# To use this spider, specify a single start URL which is the location of the store's API path of:
# /commerce/storefront/locationUsageTypes/DL/locations


class KiboSpider(Spider, AutomaticSpiderGenerator):
    page_size = 1000

    def start_requests(self):
        yield JsonRequest(url=f"{self.start_urls[0]}?pageSize={self.page_size}")

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            item = DictParser.parse(location)

            item["ref"] = location["code"]
            item["city"] = location["address"]["cityOrTown"]
            item["state"] = location["address"]["stateOrProvince"]
            item["postcode"] = location["address"]["postalOrZipCode"]
            if "email" in location["shippingOriginContact"]:
                item["email"] = location["shippingOriginContact"]["email"]
            if not item["phone"] and "phoneNumber" in location["shippingOriginContact"]:
                item["phone"] = location["shippingOriginContact"]["phoneNumber"]

            oh = OpeningHours()
            for day in DAYS_FULL:
                hours_for_day = location["regularHours"][day.lower()]
                if not hours_for_day["isClosed"]:
                    oh.add_range(day, hours_for_day["openTime"], hours_for_day["closeTime"])
            item["opening_hours"] = oh.as_opening_hours()

            yield from self.parse_item(item, location) or []

            self.page_size = response.json()["pageSize"]
            locations_remaining = response.json()["totalCount"] - (response.json()["startIndex"] + self.page_size)
            if locations_remaining > 0:
                next_start_index = response.json()["startIndex"] + self.page_size
                yield JsonRequest(url=f"{self.start_urls[0]}?pageSize={self.page_size}&startIndex={next_start_index}")

    def parse_item(self, item, location, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        if response.xpath('//script[@id="data-mz-preload-apicontext"]'):
            return True
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict:
        start_url = "https://" + urlparse(response.url).netloc + "/api/commerce/storefront/locationUsageTypes/SP/locations"
        return {
            "start_urls": [start_url],
        }
