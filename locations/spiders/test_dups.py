from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.items import Feature


class TestDupsSpider(Spider):
    name = "test_dups"
    item_attributes = {"extras": {"shop": "no"}}
    start_urls = ["data:,"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield Feature(ref="a")
        for _ in range(100):
            yield Feature(ref="b")
        for _ in range(10):
            yield Request(url="data:,1", callback=self.parse_nop)

    def parse_nop(self, response: Response, **kwargs: Any) -> Any:
        pass
