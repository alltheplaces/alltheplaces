import json
from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response
from scrapy.selector import Selector

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RioSeoSpider(Spider):
    dataset_attributes = {"source": "api", "api": "rio_seo"}

    end_point: str = None
    radius: int = 10000
    limit: int = 3000

    def start_requests(self) -> Iterable[Request]:
        if self.start_urls:
            for url in self.start_urls:
                yield JsonRequest(url=url)
        else:
            yield JsonRequest(url=urljoin(self.end_point, "getAutocompleteData"), callback=self.parse_autocomplete)

    def parse_autocomplete(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url=urljoin(
                self.end_point,
                "getAsyncLocations?template=search&level=search&search={}&radius={}&limit={}".format(
                    response.json()["data"][0], self.radius, self.limit
                ),
            )
        )

    def parse(self, response, **kwargs):
        map_list = response.json()["maplist"]
        data = json.loads("[{}]".format(Selector(text=map_list).xpath("//div/text()").get()[:-1]))
        for location in data:
            feature = DictParser.parse(location)
            feature["name"] = location["location_name"]
            feature["ref"] = "{}_{}".format(location["fid"], location["lid"])
            feature["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            feature["phone"] = location["local_phone"]
            feature["extras"]["ref:google"] = location.get("google_place_id")

            if location.get("hours_sets:primary"):
                hours = json.loads(location["hours_sets:primary"])
                if hours.get("days"):
                    feature["opening_hours"] = self.parse_hours(hours["days"])

            yield from self.post_process_feature(feature, location) or []

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        yield feature

    def parse_hours(self, store_hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()

        for weekday, intervals in store_hours.items():
            for interval in intervals:
                if not isinstance(interval, dict):
                    continue
                opening_hours.add_range(weekday, interval["open"], interval["close"])

        return opening_hours
