from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.open_graph_parser import OpenGraphParser


class OpenGraphSpider(Spider):
    dataset_attributes = {"source": "open_graph"}
    wanted_types = ["place", "business.business", "store"]

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        yield from self.parse_og(response)

    def parse_og(self, response: Response) -> Iterable[Feature]:  # noqa: C901
        og = OpenGraphParser()
        properties = og.extract_properties(response)
        if "type" in properties:
            if properties["type"] in self.wanted_types:
                item = og.as_item(properties, response)
                yield from self.post_process_item(item, response) or []

    def post_process_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
