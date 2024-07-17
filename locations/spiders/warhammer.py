from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class WarhammerSpider(Spider):
    name = "warhammer"
    item_attributes = {"brand": "Warhammer", "brand_wikidata": "Q587270"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://m5ziqznq2h-dsn.algolia.net/1/indexes/prod-lazarus-store/query",
            data={
                "query": "",
                "filters": "isWarHammerStore:true",
                "getRankingInfo": False,
                "hitsPerPage": 100,
                "page": page,
                "aroundLatLng": "0,0",
            },
            headers={"x-algolia-application-id": "M5ZIQZNQ2H", "x-algolia-api-key": "92c6a8254f9d34362df8e6d96475e5d8"},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hits"]:
            item = DictParser.parse(location)
            item["website"] = None  # 404
            item["lat"] = location["_geoloc"]["lat"]
            item["lon"] = location["_geoloc"]["lng"]

            item["opening_hours"] = OpeningHours()
            for day, rule in location.get("hours", {}).items():
                if rule.get("isClosed") is True:
                    continue
                for time in rule.get("openIntervals"):
                    item["opening_hours"].add_range(day, time["start"], time["end"])

            yield item

        if response.json()["page"] < response.json()["nbPages"]:
            yield self.make_request(response.json()["page"] + 1)
