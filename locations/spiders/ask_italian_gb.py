from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class AskItalianGBSpider(Spider):
    name = "ask_italian_gb"
    item_attributes = {"brand": "ASK Italian", "brand_wikidata": "Q4807056"}
    start_urls = ["https://www.askitalian.co.uk/wp-json/locations/get_venues"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")

            item["website"] = location["link"]
            item["image"] = location["featured_image"]

            yield item
