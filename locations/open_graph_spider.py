import re
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from scrapy import Selector, Spider
from scrapy.http import Response
from locations.open_graph_parser import OpenGraphParser

from locations.items import Feature

class OpenGraphSpider(Spider):
    dataset_attributes = {"source": "open_graph"}

    def parse(self, response: Response, **kwargs):
        yield from self.parse_og(response)

    def parse_og(self, response: Response):  # noqa: C901
        item = OpenGraphParser.parse(response)
        yield from self.post_process_item(item, response) or []

    def post_process_item(self, item, response, **kwargs):
        """Override with any post-processing on the item."""
        yield item