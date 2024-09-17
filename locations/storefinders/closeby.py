from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class ClosebySpider(Spider):
    """
    Closeby is a map based storefinder, relying on a JSON API.

    Use by specifying the `api_key` spider attribute.
    """

    dataset_attributes = {"source": "api", "api": "closeby.co"}
    api_key: str = ""

    def start_requests(self):
        yield JsonRequest(url=f"https://www.closeby.co/embed/{self.api_key}/locations")

    def parse(self, response):
        for location in response.json()["locations"]:
            self.pre_process_data(location)

            item = DictParser.parse(location)
            item["addr_full"] = location.get("address_full")

            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item, response, location):
        """Override with any post-processing on the item."""
        yield item

    def pre_process_data(self, location: dict, **kwargs):
        """Override with any pre-processing on the item."""
