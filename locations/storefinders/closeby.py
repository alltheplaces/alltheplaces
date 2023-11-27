import re

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser


class ClosebySpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "closeby.co"}
    api_key = ""

    def start_requests(self):
        yield JsonRequest(url=f"https://www.closeby.co/embed/{self.api_key}/locations")

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = location.get("address_full")
            yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        if len(response.xpath('//iframe[contains(@src, "https://www.closeby.co/embed/")]')) > 0:
            return True
        elif len(response.xpath('//script[contains(@src, "https://embed.closeby.co/v1.js")]')) > 0:
            return True
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict:
        api_key = response.xpath('//iframe[contains(@src, "https://www.closeby.co/embed/")]/@src').get()
        if api_key and "/" in api_key:
            api_key = api_key.split("/")[-1]
        if not api_key:
            if api_key_match := re.search(
                r"closeby\.mapKey=([0-9a-f]{32})(?![0-9a-f])",
                response.xpath('//script[contains(@src, "https://embed.closeby.co/v1.js")]').get(),
            ):
                api_key = api_key_match.group(1)
        if api_key:
            return {
                "api_key": api_key,
            }
        else:
            return {}
