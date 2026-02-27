import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class Century21USSpider(Spider):
    name = "century_21_us"
    item_attributes = {"brand": "Century 21", "brand_wikidata": "Q1054480"}
    start_urls = ["https://www.century21.com/office/all"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    api_key = ""

    def make_request(self, place_master_id: str, page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.century21.com/api/offices?brandCode=C21&page={page}&numPerPage={page_size}&placeMasterId={place_master_id}&selectFields=officeMasterId,officeName,company,addresses,phoneNumbers,emailAccounts,socialMediaAccounts,media,doingBusinessAs,canonicalURL&descendingOrder=false&sortKey=doingBusinessAs&locationTypes=physicalLocations,areasServedLocations&displayPreferences=true",
            headers={"x-api-key": self.api_key},
            callback=self.parse_locations,
            cb_kwargs=dict(place_master_id=place_master_id, page=page, page_size=page_size),
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            url=response.xpath('//link[contains(@href, "/assets/SERVICES-")]/@href').get(),
            callback=self.parse_api_key,
        )

    def parse_api_key(self, response: Response, **kwargs: Any) -> Any:
        self.api_key = re.search(r"\"x-api-key\"[\s:]+\"(\w+)\"", response.text).group(1)
        yield JsonRequest(
            url="https://www.century21.com/api/places/search",
            data={
                "brand": "C21",
                "placeType": "state",
                "numPerPage": 100,
                "page": 1,
                "projectedFields": "placeMasterId,placeName,displayName,canonicalUrl",
            },
            headers={"x-api-key": self.api_key},
            callback=self.parse_states,
        )

    def parse_states(self, response: Response, **kwargs: Any) -> Any:
        for result in response.json()["data"]["results"]:
            yield self.make_request(result["placeMasterId"], 1)

    def parse_locations(self, response: Response, place_master_id: str, page: int, page_size: int) -> Any:
        for location in response.json()["data"].get("results", []):
            item = DictParser.parse(location)
            item["image"] = location["photo"]
            item["website"] = urljoin("https://www.century21.com/office/detail/", location["canonicalUrl"])
            yield item

        if page * page_size < response.json()["data"]["pagination"]["totalResults"]:
            yield self.make_request(place_master_id, page + 1, page_size)
