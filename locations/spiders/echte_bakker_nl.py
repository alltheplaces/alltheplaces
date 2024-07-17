from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class EchteBakkerNLSpider(Spider):
    name = "echte_bakker_nl"
    item_attributes = {"brand": "De Echte Bakker", "brand_wikidata": "Q16920716"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(url="https://echtebakker.nl/api/fetchDealers?page={}".format(page), meta={"page": page})

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.meta["page"] < response.json()["lastPage"]:
            yield self.make_request(response.meta["page"] + 1)

        if isinstance(response.json()["data"], list):
            locations = response.json()["data"]
        elif isinstance(response.json()["data"], dict):
            locations = response.json()["data"].values()

        for location in locations:
            item = DictParser.parse(location)
            item["lat"] = (location["address"] or {}).get("latitude")
            item["lon"] = (location["address"] or {}).get("longitude")

            item["opening_hours"] = OpeningHours()
            for day, times in location["opening_hours"].items():
                if day == "exceptions":
                    continue
                for time in times:
                    item["opening_hours"].add_range(day, *time.split("-"))

            yield item
