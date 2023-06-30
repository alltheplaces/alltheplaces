import base64
import json
import re
import zlib

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.items import Feature


class LocatedMapSpider(Spider):
    dataset_attributes = {"source": "api", "api": "app.locatedmap.com"}

    lm_key = None

    def start_requests(self):
        yield Request(
            url=f"https://app.locatedmap.com/widget/?compId=comp-ksrvm7jz&viewMode=site&instance={self.lm_key}"
        )

    def parse(self, response, **kwargs):
        if m := re.search(r"let l = \"{\'base64\': \'(.+)\'}\"", response.text):
            compressed_data = base64.b64decode(m.group(1).encode("ascii"))
            data = json.loads(zlib.decompress(compressed_data))

            for location in data:
                item = DictParser.parse(location)
                item["ref"] = location["pKey"]
                item["addr_full"] = location["formatted_address"]

                yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
