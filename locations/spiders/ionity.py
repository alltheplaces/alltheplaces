import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class IonitySpider(Spider):
    name = "ionity"
    item_attributes = {"brand": "Ionity", "brand_wikidata": "Q42717773"}
    start_urls = ["https://www.ionity.eu/network"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        json_url = re.search(r"MAP_DATA\s*:\s*\"(.+)\",\s*", response.text).group(1)
        yield JsonRequest(url=json_url, callback=self.parse_locations)

    def parse_locations(self, response):
        for location in response.json()["LocationDetails"]:
            item = DictParser.parse(location)
            item["ref"] = item["name"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
