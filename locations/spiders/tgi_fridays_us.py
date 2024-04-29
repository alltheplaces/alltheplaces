import json
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class TGIFridaysUSSpider(Spider):
    name = "tgi_fridays_us"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="https://liveapi.yext.com/v2/accounts/me/answers/vertical/query?{}".format(
                urlencode(
                    {
                        "experienceKey": "tgi-fridays-search",
                        "api_key": "96b4f9cb0c9c2f050eeec613af5b5340",
                        "v": "20220511",
                        "version": "PRODUCTION",
                        "locale": "en",
                        "verticalKey": "locations",
                        "filters": json.dumps(
                            {"builtin.location": {"$near": {"lat": 0, "lng": 0, "radius": 50000000}}}
                        ),
                        "limit": "50",
                        "offset": str(offset),
                        "source": "STANDARD",
                    }
                )
            ),
            meta={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["results"]:
            item = DictParser.parse(location["data"])
            item["branch"] = location["data"]["geomodifier"]
            item["extras"]["ref:google"] = location["data"].get("googlePlaceId")
            item["facebook"] = location["data"].get("facebookPageUrl")

            item["opening_hours"] = self.parse_opening_hours(location)

            yield from self.parse_item(location, item) or []

        if len(response.json()["response"]["results"]) == 50:
            yield self.make_request(response.meta["offset"] + 50)

    def parse_opening_hours(self, location, **kwargs: Any) -> OpeningHours | None:
        oh = OpeningHours()
        for day, rule in location["data"]["hours"].items():
            if rule.get("isClosed") is True:
                continue
            for time in rule["openIntervals"]:
                oh.add_range(day, time["start"], time["end"])

        return oh

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
