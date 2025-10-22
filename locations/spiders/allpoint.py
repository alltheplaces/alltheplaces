from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class AllpointSpider(Spider):
    name = "allpoint"
    item_attributes = {"brand": "Allpoint", "brand_wikidata": "Q4733264"}
    total_count = 0
    page_size = 0
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    def make_request(self, page: int) -> JsonRequest:
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

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        results = response.json()["data"]
        if not self.total_count:
            # Initialize total_count and page_size only once, when data is available
            self.total_count = results["TotalRecCount"]
            self.page_size = results["PageSize"]

        locations = results.get("ATMInfo") or []
        for atm in locations:
            item = DictParser.parse(atm)
            item["street_address"] = item.pop("street", None)
            yield item

        if (kwargs["current_page"] * self.page_size) < self.total_count:
            yield self.make_request(kwargs["current_page"] + 1)
