import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class TestSpider(Spider):
    name = "test"
    item_attributes = {"brand": "KKM", "brand_wikidata": "Q57515549"}
    start_urls = ["https://kkm.krakow.pl/pl/punkty-sprzedazy-biletow/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_raw in re.findall(r"items\.push\(\s+({.+?})\)", response.text, re.DOTALL):
            location = chompjs.parse_js_object(re.sub(r"\s:", ":", location_raw))
            item = Feature()
            item["ref"] = location["Id"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            print(location)  # TODO: address? TypeId/TypeName
            yield item
