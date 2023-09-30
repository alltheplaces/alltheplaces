from urllib.parse import quote_plus

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# API documentation available at:
# https://admin.metalocator.com/components/com_locator/assets/documents/api/classes/LocatorControllerAPI.html#method_search
#
# To use this spider, specify a brand_id (Itemid in API URLs)
# as well as one or more country names in the country_list array.


class MetaLocatorSpider(Spider):
    dataset_attributes = {"source": "api", "api": "metalocator.com"}
    brand_id = None
    country_list = []
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for country in self.country_list:
            country_urlsafe = quote_plus(country)
            yield JsonRequest(
                url=f"https://code.metalocator.com/webapi/api/search/?Itemid={self.brand_id}&country={country_urlsafe}&limit=1000000"
            )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("addr_full")
            item["street_address"] = ", ".join(filter(None, [location["address"], location["address2"]]))
            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["hours"].replace("|", " "))
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
