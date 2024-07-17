import json
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class YextAnswersSpider(Spider):
    dataset_attributes = {"source": "api", "api": "yext"}

    endpoint: str = "https://liveapi.yext.com/v2/accounts/me/answers/vertical/query"
    api_key: str = ""
    experience_key: str = ""
    api_version: str = "20220511"
    page_limit: int = 50
    locale: str = "en"
    environment: str = "PRODUCTION"  # "STAGING" also used
    feature_type: str = "locations"  # "restaurants" also used

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="{}?{}".format(
                self.endpoint,
                urlencode(
                    {
                        "experienceKey": self.experience_key,
                        "api_key": self.api_key,
                        "v": self.api_version,
                        "version": self.environment,
                        "locale": self.locale,
                        "verticalKey": self.feature_type,
                        "filters": json.dumps(
                            {"builtin.location": {"$near": {"lat": 0, "lng": 0, "radius": 50000000}}}
                        ),
                        "limit": str(self.page_limit),
                        "offset": str(offset),
                        "source": "STANDARD",
                    }
                ),
            ),
            meta={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["results"]:
            item = DictParser.parse(location["data"])
            item["branch"] = location["data"].get("geomodifier")
            item["extras"]["ref:google"] = location["data"].get("googlePlaceId")
            item["facebook"] = location["data"].get("facebookPageUrl")

            if website_url_dict := location["data"].get("websiteUrl"):
                if website_url_dict.get("preferDisplayUrl"):
                    item["website"] = website_url_dict.get("displayUrl")
                else:
                    item["website"] = website_url_dict.get("url")

            if (
                not isinstance(item["lat"], float)
                or not isinstance(item["lon"], float)
                and location["data"].get("yextDisplayCoordinate")
            ):
                item["lat"] = location["data"]["yextDisplayCoordinate"].get("latitude")
                item["lon"] = location["data"]["yextDisplayCoordinate"].get("longitude")

            item["opening_hours"] = self.parse_opening_hours(location)

            yield from self.parse_item(location, item) or []

        if len(response.json()["response"]["results"]) == self.page_limit:
            yield self.make_request(response.meta["offset"] + self.page_limit)

    def parse_opening_hours(self, location: dict, **kwargs: Any) -> OpeningHours | None:
        oh = OpeningHours()
        hours = location["data"].get("hours")
        if not hours:
            return None
        for day, rule in hours.items():
            if not isinstance(rule, dict):
                continue
            if day == "holidayHours":
                continue
            if rule.get("isClosed") is True:
                continue
            for time in rule["openIntervals"]:
                oh.add_range(day, time["start"], time["end"])

        return oh

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
