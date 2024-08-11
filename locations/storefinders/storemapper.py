from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class StoremapperSpider(Spider):
    """
    Storemapper (https://www.storemapper.com/) is an emedded map based store locator.

    API docs are available via https://help.storemapper.com/category/4313-advanced-settings-and-customisation

    Use by specifying a `key`
    """

    dataset_attributes = {"source": "api", "api": "storemapper.com"}

    key = ""
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(url=f"https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/{self.key}/stores.js")

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
