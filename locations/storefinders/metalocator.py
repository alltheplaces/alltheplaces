from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# API documentation available at:
# https://admin.metalocator.com/components/com_locator/assets/documents/api/classes/LocatorControllerAPI.html#method_search
#
# To use this spider, specify a brand_id (Itemid in API URLs).


class MetaLocatorSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "metalocator.com"}
    brand_id: str = None
    custom_settings = {"ROBOTSTXT_OBEY": False}
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/(?:admin|code)\.metalocator\.com\/index\.php\?.*?(?<=[?&])Itemid=(?P<brand_id>\d+)(?:&|$)"
        ),
        DetectionResponseRule(js_objects={"brand_id": r"window.ml___Itemid.toString()"}),
        DetectionResponseRule(js_objects={"brand_id": r"window.ml_search_geography.itemid.toString()"}),
    ]

    def start_requests(self):
        yield JsonRequest(url=f"https://code.metalocator.com/webapi/api/search/?Itemid={self.brand_id}&limit=100000")

    def parse(self, response: Response):
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("addr_full")
            item["street_address"] = ", ".join(filter(None, [location["address"], location["address2"]]))
            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["hours"].replace("|", " "))
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
