import json
from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response
from scrapy.selector import Selector

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RioSeoSpider(Spider, AutomaticSpiderGenerator):
    """
    RioSEO is a number of related storefinders.
    https://www.rioseo.com/platform/local-pages/

    To use, specify:
      - `end_point`: mandatory parameter, should be a URL containing the path
        `/api/getAsyncLocations` and including parameters similar to
        `?template=search&level=search`
      - `radius`: optional parameter, default value is 10000
      - `limit`: optional parameter, default valus is 3000
    """

    dataset_attributes = {"source": "api", "api": "rio_seo"}
    end_point: str = None
    radius: int = 10000
    limit: int = 3000
    detection_rules = [
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/api\/getAsyncLocations\?.+)$"
        )
    ]

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
        try:
            data = json.loads("[{}]".format(Selector(text=map_list).xpath("//div/text()").get()[:-1]))
        except json.decoder.JSONDecodeError:
            self.logger.warning("Could not parse response - check API output")
            data = []
        except TypeError:
            data = []

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
