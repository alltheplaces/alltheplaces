from json import JSONDecodeError, loads
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class RioSeoSpider(Spider):
    """
    RioSEO is a number of related storefinders.
    https://www.rioseo.com/platform/local-pages/

    To use, specify:
      - `end_point`: mandatory parameter, should be a URL containing the path
        `/api/getAsyncLocations` and including parameters similar to
        `?template=search&level=search`
      - `template`: mandatory parameter, should be either "domain" or "search"
      - `radius`: optional parameter, default value is 20038
      - `limit`: optional parameter, default value is 10000
    """

    dataset_attributes: dict = {"source": "api", "api": "rio_seo"}

    end_point: str | None = None
    limit: int = 10000
    radius: int = 20038
    template: str = "domain"

    async def start(self) -> AsyncIterator[JsonRequest]:
        if self.end_point is None:
            raise ValueError("The 'end_point' attribute must be specified.")
            return
        if self.template not in ["domain", "search"]:
            raise ValueError("The 'template' attribute must be specified as either 'domain' or 'search'.")
            return
        yield JsonRequest(
            f"{self.end_point}/api/getAutocompleteData?template={self.template}&level={self.template}",
            callback=self.parse_autocomplete,
        )

    def parse_autocomplete(self, response: TextResponse, **kwargs: Any) -> Iterable[JsonRequest]:
        yield JsonRequest(
            f"{self.end_point}/api/getAsyncLocations?template={self.template}&level={self.template}&search={response.json()['data'][0]}&radius={self.radius}&limit={self.limit}"
        )

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        map_list = response.json()["maplist"]
        if map_list == "":
            return
        map_list = map_list.removeprefix('<div class="tlsmap_list">')
        map_list = map_list.removesuffix(",</div>")
        map_list = map_list.replace("\t", " ")
        data = loads(f"[{map_list}]")

        if len(data) == self.limit:
            self.logger.warning(f"Received {len(data)} entries, the limit may need to be raised")

        for location in data:
            feature = DictParser.parse(location)
            feature["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            feature["ref"] = location["fid"]
            feature["phone"] = location["local_phone"]
            feature["image"] = location.get("location_image")
            feature["located_in"] = location.get("shopping_center_name", location.get("location_shopping_center"))
            feature["extras"]["start_date"] = location.get("opening_date", location.get("grand_opening_date"))

            if hours := location.get("hours_sets:primary"):
                feature["opening_hours"] = self.parse_hours(hours)

            if location.get("location_closure_message"):
                set_closed(feature)

            yield from self.post_process_feature(feature, location) or []

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        yield feature

    def parse_hours(self, hours: dict | str) -> OpeningHours | None:
        if isinstance(hours, str):
            try:
                hours = loads(hours)
            except JSONDecodeError:
                self.logger.warning(f"Could not parse hours: {hours!r}")
                return

        days = hours.get("days")
        if not days:
            return

        opening_hours = OpeningHours()

        for weekday, intervals in days.items():
            if intervals == "open24":
                opening_hours.add_range(weekday, "00:00", "23:59")
            else:
                for interval in intervals:
                    if not isinstance(interval, dict):
                        continue
                    opening_hours.add_range(weekday, interval["open"], interval["close"])

        return opening_hours
