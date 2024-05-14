from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class YextSearchSpider(Spider):
    dataset_attributes = {"source": "api", "api": "yext"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    host: str = "https://locator.chick-fil-a.com.yext-cdn.com"
    page_size: int = 50

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest("{}/search?r=250000&per={}&offset={}".format(self.host, self.page_size, offset))

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["entities"]:
            item = Feature()
            item["city"] = location["profile"]["address"]["city"]
            item["country"] = location["profile"]["address"]["countryCode"]
            item["street_address"] = merge_address_lines(
                [
                    location["profile"]["address"]["line1"],
                    location["profile"]["address"]["line2"],
                    location["profile"]["address"]["line3"],
                ]
            )
            item["postcode"] = location["profile"]["address"]["postalCode"]
            item["state"] = location["profile"]["address"]["region"]

            item["name"] = location["profile"]["name"]
            coords = location["profile"].get("displayCoordinate") or location["profile"].get("yextDisplayCoordinate")
            item["lat"] = coords["lat"]
            item["lon"] = coords["long"]
            item["website"] = location["profile"].get("websiteUrl", "").split("?", 1)[0]
            item["ref"] = location["url"]

            yield from self.parse_item(location, item) or []

        pager = response.json()["queryParams"]
        offset = int(pager["offset"][0])
        page_size = int(pager["per"][0])
        if offset + page_size < response.json()["response"]["count"]:
            yield self.make_request(offset + page_size)

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
