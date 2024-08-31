import json
from typing import Any, Iterable, Optional

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class RioSeoSpider(Spider):
    """
    RioSEO is a number of related storefinders.
    https://www.rioseo.com/platform/local-pages/

    To use, specify `end_point` as the API endpoint, usually starting with
    "maps.", and omitting the path starting with /api
    """

    dataset_attributes = {"source": "api", "api": "rio_seo"}

    end_point: Optional[str] = None
    limit: int = 10000
    radius: int = 20038
    template: str = "domain"

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(f"{self.end_point}/api/getAutocompleteData", callback=self.parse_autocomplete)

    def parse_autocomplete(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            f"getAsyncLocations?template={self.template}&level={self.template}&search={response.json()['data'][0]}&radius={self.radius}&limit={self.limit}"
        )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        map_list = response.json()["maplist"]
        if map_list == "":
            return
        map_list = map_list.removeprefix('<div class="tlsmap_list">')
        map_list = map_list.removesuffix(",</div>")
        map_list = map_list.replace("\t", " ")
        data = json.loads(f"[{map_list}]")

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
                hours = json.loads(hours)
            except json.decoder.JSONDecodeError:
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
