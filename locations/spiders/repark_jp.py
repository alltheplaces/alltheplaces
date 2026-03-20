from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import city_locations, country_iseadgg_centroids

RADIUS_KM = 24


class ReparkJPSpider(Spider):
    name = "repark_jp"
    item_attributes = {"brand_wikidata": "Q55521368"}

    def make_request(self, lat, lon):
        return JsonRequest(f"https://www.repark.jp/ajax/time_markers.json?range=C{lat},{lon}N90W0S0E180")

    async def start(self):
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon)
        for city in city_locations("JP"):
            yield self.make_request(city["latitude"], city["longitude"])

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for loc in response.json():
            item = DictParser.parse(loc)
            item["ref"] = loc["park_code"]
            item["name"] = loc["park_name"]
            item["extras"]["capacity"] = loc["capacity"]
            item["extras"]["maxheight"] = loc["height_limit"]
            item["extras"]["maxwidth"] = loc["width_limit"]
            item["extras"]["maxlength"] = loc["length_limit"]
            item["extras"]["maxweight"] = loc["weight_limit"]
            item["website"] = f"https://www.repark.jp/parking_user/time/result/detail/?park={loc['park_code']}"

            yield item
