from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature

# This store finder is a software-as-a-service application with a
# web site of https://storelocatorplus.com/
#
# This store finder is not to be confused with the self-hosted
# WordPress plugin of the same name, from the same company, that is
# documented at https://wordpress.org/plugins/store-locator-le/
#
# To use this spider, specify two attributes: `slp_dataset` and
# `slp_key`. If you need to parse additional fields or clean any
# data returned, override the `parse_item` function.


class StoreLocatorPlusCloudSpider(Spider):
    dataset_attributes = {"source": "api", "api": "storelocatorplus.com"}
    slp_dataset: str = None
    slp_key: str = None

    def start_requests(self):
        yield JsonRequest(
            url=f"https://dashboard.storelocatorplus.com/{self.slp_dataset}/wp-json/myslp/v2/locations-map/search?action=csl_ajax_onload&api_key={self.slp_key}"
        )

    def parse(self, response: Response):
        if not response.json()["data"]["success"]:
            return

        for location in response.json()["data"]["response"]:
            item = DictParser.parse(location)
            item["addr_full"] = None
            item["street_address"] = ", ".join(filter(None, [location["address2"], location["address"]]))

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
