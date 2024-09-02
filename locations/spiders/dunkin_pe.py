import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.dunkin_us import DunkinUSSpider


class DunkinPESpider(Spider):
    name = "dunkin_pe"
    item_attributes = DunkinUSSpider.item_attributes
    start_urls = ["https://dunkin.pe/locales"]

    custom_settings = {
        "COOKIES_ENABLED": False,
    }
    requires_proxy = True

    def parse(self, response, **kwargs):
        token = re.search(r"sessionToken:\"(\w+)\"", response.text)
       if token is None:
           return

       yield JsonRequest(
            url="https://amyseo5s3g.execute-api.us-east-1.amazonaws.com/pro/api/stores/tags",
            headers={"x-api-key": "khvA1yr24D8ilyeHKLfpF6ICDiKyGaU1912fcDO9"},
            data={"section": "locales", "session_token": token.group(1)},
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json()["data"]["stores"]:
            location["ref"] = location["storelocator_id"]
            location["street_address"] = location.pop("address")
            location["lon"] = location["longtitude"]
            location["city"] = location["tag"]
            yield DictParser.parse(location)
