import re
from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class LunchGardenBESpider(Spider):
    name = "lunch_garden_be"
    item_attributes = {"brand": "Lunch Garden", "brand_wikidata": "Q2491217"}
    start_urls = ["https://www.lunchgarden.be/nl/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        url_path = response.xpath('//*[@type="application/json"]//@data-src').get()
        yield scrapy.Request(url=urljoin(response.url, url_path), callback=self.parse_location)

    def parse_location(self, response, **kwargs):
        pattern = r'\"([^\"]+)\",\s*"([^\"]+)\",\s*\{\"lat\":\d+,\"lng\":\d+\},\s*([\d.]+),\s*([\d.]+),.*?\"([^\"]+)\",\s*\"([^\"]+)\",\s*"([^\"]+)\"'
        matches = re.findall(pattern, response.text, re.DOTALL)
        if matches:
            for location in matches:
                item = Feature()
                item["branch"] = location[4].removeprefix("Lunch Garden ")
                item["addr_full"] = location[1]
                item["lat"] = location[2]
                item["lon"] = location[3]
                item["website"] = item["ref"] = "https://www.lunchgarden.be/nl/restaurants/" + location[-1]
                yield item
