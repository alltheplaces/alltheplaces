from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ImoSpider(Spider):
    name = "imo"
    item_attributes = {"brand_wikidata": "Q1654122"}
    start_urls = ["https://www.imocarwash.com/umbraco/api/location/get"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Markers"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("IMO Car Wash ")
            item["website"] = urljoin("https://www.imocarwash.com/", location["Url"])
            yield item
