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
        pattern = r"\"([^\"]+,\s*\d{4}\s*[^\"]+)\".*?\{\s*\"lat\"\s*:\s*\d+,\s*\"lng\"\s*:\s*\d+\s*\}\s*,\s*([\d.]+)\s*,\s*([\d.]+).*?\"(Lunch Garden[^\"]+)\".*?\"([a-z0-9-]+)\""
        matches = re.findall(pattern, response.text, re.DOTALL)
        if matches:
            for location in matches:
                item = Feature()
                item["branch"] = location[3].removeprefix("Lunch Garden ")
                item["addr_full"] = location[0]
                item["lat"] = location[1]
                item["lon"] = location[2]
                item["website"] = item["ref"] = "https://www.lunchgarden.be/nl/restaurants/" + location[-1]
                yield item
