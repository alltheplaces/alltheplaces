from typing import Iterable

import scrapy
from scrapy import Request

from locations.dict_parser import DictParser


class PradaSpider(scrapy.Spider):
    name = "prada"
    item_attributes = {"brand": "Prada", "brand_wikidata": "Q193136"}

    def make_request(self, offset: int):
        return scrapy.Request(
            url="https://cdn.yextapis.com/v2/accounts/me/search/vertical/query?api_key=61119b3d853ae12bf41e7bd9501a718b&v=20220511&limit=50&experienceKey=prada-experience&verticalKey=prada-locations&retrieveFacets=true&offset={}".format(
                offset
            ),
            cb_kwargs={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response, **kwargs):
        if raw_data := response.json()["response"]["results"]:
            for store in raw_data:
                item = DictParser.parse(store["data"])
                item["website"] = "https://www.prada.com/us/en/store-locator/" + store["data"]["slug"]
                yield item
            current_offeset = kwargs["offset"] + 50
            yield self.make_request(current_offeset)
