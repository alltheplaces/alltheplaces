from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature


class StoremapperSpider(Spider):
    """
    Storemapper (https://www.storemapper.com/) is an embedded map based store
    locator. API documentation is available at:
    https://help.storemapper.com/category/4313-advanced-settings-and-customisation

    To use this store finder, specify a company_id as a string. This
    company_id is usually a single integer, but can sometimes also have a
    suffix (separated with a hyphen) that contains word characters (e.g.
    a-zA-Z0-9 observed to be used if a suffix is included).

    If clean ups or additional field extraction is required from the source
    data, override the parse_item function. Two parameters are passed:
    - item: an ATP "Feature" class
    - location: a dictionary which is returned from the store locator JSON
    response for a particular location
    """

    dataset_attributes: dict = {"source": "api", "api": "storemapper.com"}
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}

    company_id: str

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/{self.company_id}/stores.js"
        )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
