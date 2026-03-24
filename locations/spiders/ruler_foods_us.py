from typing import Iterable

import scrapy
from requests import Response
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class RulerFoodsUSSpider(scrapy.Spider):
    name = "ruler_foods_us"
    item_attributes = {"brand": "Ruler Foods", "brand_wikidata": "Q17125470"}
    allowed_domains = ["falcon.shop.inmar.io"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self):
        yield JsonRequest(
            url="https://falcon.shop.inmar.io/v2/locations?fulfillmentMethod=instore",
            headers={"Inmar-Session-Id": "1MyVgoGgwdgZWxlNcPEREQ"},
        )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for location in response.json()["data"]["item"]["modules"]["itemListModules"][0]["items"]["locationItems"]:
            location.update(location.pop("locationAddress"))
            item = DictParser.parse(location)
            yield item
