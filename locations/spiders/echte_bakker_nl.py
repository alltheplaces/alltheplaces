from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class EchteBakkerNLSpider(Spider):
    name = "echte_bakker_nl"
    item_attributes = {"brand": "De Echte Bakker", "brand_wikidata": "Q16920716"}
    start_urls = ["https://echtebakker.nl/api/fetch-dealers"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["name"], item["branch"] = item.pop("name").split(" - ")
            item["name"] = item["name"].split(", ")[0]
            item["street_address"] = item.pop("addr_full")
            yield item
