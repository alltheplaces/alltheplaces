import json
from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class RomanOriginalsGBSpider(Spider):
    name = "roman_originals_gb"
    item_attributes = {"brand": "Roman Originals", "brand_wikidata": "Q94579553"}
    start_urls = ["https://www.roman.co.uk/store-locator"]

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = self.find_between(response.text, '"@graph":', "}</script>")
        json_data = json.loads(data)
        for stores in json_data:
            if stores["@type"] == "Store":
                for store in stores["department"]:
                    item = DictParser.parse(store)
                    item["ref"] = store["areaServed"][0]["name"][0]
                    item["branch"] = item["ref"]
                    item["website"] = urljoin("https://www.roman.co.uk", store["url"])
                    item["lat"] = store["location"]["geo"]["latitude"]
                    item["lon"] = store["location"]["geo"]["longitude"]

                    yield item
