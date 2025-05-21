from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class TestDupsSpider(Spider):
    name = "test_dups"
    start_urls = ["data:,"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield Feature(ref="a")
        yield Feature(ref="a")
        yield Feature(ref="b")
