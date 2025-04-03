from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class AllpointSpider(Spider):
    name = "allpoint"
    item_attributes = {"brand": "Allpoint", "brand_wikidata": "Q4733264"}
    download_timeout = 50

    def make_request(self, page: int) -> Request:
        return JsonRequest(
            url="https://clsws.locatorsearch.net/Rest/LocatorSearchAPI.svc/GetLocations",
            data={
                "NetworkId": 10029,
                "Latitude": 33.15004936,
                "Longitude": -96.83464,
                "Miles": 50000,
                "SearchByOptions": "ATMSF, ATMDP",
                "PageIndex": page,
            },
            cb_kwargs={"current_page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.json()["data"]["ATMInfo"]:
            for atm in response.json()["data"]["ATMInfo"]:
                item = DictParser.parse(atm)
                item["street_address"] = item.pop("street", None)
                yield item
            yield self.make_request(kwargs["current_page"] + 1)
