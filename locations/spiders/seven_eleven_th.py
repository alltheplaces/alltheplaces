from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations


class SevenElevenThSpider(scrapy.Spider):
    name = "seven_eleven_th"
    start_urls = ["https://7eleven-api-prod.jenosize.tech/v1/Store/GetStoreByCurrentLocation"]
    requires_proxy = "TH"
    custom_settings = {
        # The website may block the spider
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self) -> Iterable[Request]:
        for city in city_locations("TH"):
            payload = {
                "latitude": city.get("latitude"),
                "longitude": city.get("longitude"),
                "products": [],
                "distance": 10000000,
                "limit": 10000000,
            }
            yield JsonRequest("https://7eleven-api-prod.jenosize.tech/v1/Store/GetStoreByCurrentLocation", data=payload)

    def parse(self, response):
        for poi in response.json().get("data", []):
            item = DictParser.parse(poi)
            item["name"] = None
            item["branch"] = poi.get("name")
            item['extras']['addr:district'] = poi.get("district")
            item['extras']['addr:subdistrict'] = poi.get("subdistrict")
            yield item
