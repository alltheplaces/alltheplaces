import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class Century21Spider(scrapy.Spider):
    name = "century_21"
    item_attributes = {"brand": "Century 21", "brand_wikidata": "Q1054480"}

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.century21global.com/api/aggregator-service/aggregator/office",
            headers={"Content-Type": "application/json"},
            data={"offset": offset, "max": 40, "includeListings": False, "language": "EN"},
            cb_kwargs={"offset": offset},
        )

    def start_requests(self):
        yield self.make_request(0)

    def parse(self, response, **kwargs):
        if response.json()["result"]:
            for office in response.json()["result"]:
                item = DictParser.parse(office)
                item["street_address"] = item.pop("street")
                item["website"] = "https://www.century21global.com/"
                yield item
            current_offeset = kwargs["offset"] + 40
            yield self.make_request(current_offeset)
