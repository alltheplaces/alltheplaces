from typing import Iterable
from urllib.parse import urlencode

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class YextLocationsSpider(Spider):
    dataset_attributes = {"source": "api", "api": "yext"}

    endpoint: str = "https://cdn.yextapis.com/v2/accounts/me/content/locations"
    api_key: str = ""
    api_version: str = "20231114"
    page_limit: int = 50

    def make_request(self, page_token: str) -> JsonRequest:
        return JsonRequest(
            url="{}?{}".format(
                self.endpoint,
                urlencode(
                    {
                        "api_key": self.api_key,
                        "v": self.api_version,
                        "limit": str(self.page_limit),
                        "pageToken": page_token,
                    }
                ),
            )
        )

    def start_requests(self) -> Iterable[JsonRequest]:
        yield self.make_request("")

    def parse(self, response: Response) -> Iterable[Feature | JsonRequest]:
        for location in response.json()["response"]["docs"]:
            item = DictParser.parse(location)
            item["branch"] = location.get("geomodifier")
            YextAnswersSpider.parse_socials(item, location)
            item["opening_hours"] = YextAnswersSpider.parse_opening_hours(location.get("hours"))
            yield from self.parse_item(location, item) or []

        if next_page_token := response.json()["response"].get("nextPageToken"):
            yield self.make_request(next_page_token)

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
