from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature


class StoreLocatorPlusSpider(Spider):
    dataset_attributes = {"source": "api", "api": "storelocatorplus.com"}

    slp_dataset = None
    slp_key = None

    def start_requests(self):
        yield JsonRequest(
            url=f"https://dashboard.storelocatorplus.com/{self.slp_dataset}/wp-json/myslp/v2/locations-map/search?action=csl_ajax_onload&api_key={self.slp_key}"
        )

    def parse(self, response, **kwargs):
        if not response.json()["data"]["success"]:
            return

        for location in response.json()["data"]["response"]:
            location["street_address"] = ", ".join(filter(None, [location.pop("address2"), location.pop("address")]))

            item = DictParser.parse(location)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
