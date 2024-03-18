import json
from typing import Iterable

from scrapy import Spider
from scrapy.selector import Selector

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RioSeoSpider(Spider):
    dataset_attributes = {"source": "api", "api": "rio_seo"}

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
