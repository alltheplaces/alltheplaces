from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenTHSpider(scrapy.Spider):
    """
    Store locator: https://www.7eleven.co.th/find-store
    """

    name = "seven_eleven_th"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    requires_proxy = "TH"
    custom_settings = {
        # The website may block the spider
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self) -> Iterable[Request]:
        # TODO: better way to iterate over geo-based API, only half of the POIs are fetched.
        #       Small towns are not present in geonamescache.
        #       Big cities are not fully covered due to big area.
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
            item["extras"]["addr:district"] = poi.get("district")
            item["extras"]["addr:subdistrict"] = poi.get("subdistrict")
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
