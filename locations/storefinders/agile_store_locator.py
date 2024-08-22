import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class AgileStoreLocatorSpider(Spider):
    """
    Official documentation for Agile Store Locator:
    https://agilestorelocator.com/documentation/

    To use this store finder, specify allowed_domains = [x, y, ..] (either one
    or more domains such as example.net) and the default path for the Agile
    Store Locator API endpoint will be used. In the event the default path is
    different, you can alternatively specify one or more
    start_urls = [x, y, ..].

    If clean ups or additional field extraction is required from the source
    data, override the parse_item function. Two parameters are passed, item
    (an ATP "Feature" class) and feature (a dict which is returned from the
    store locator JSON response for a particular feature).
    """

    time_format = "%I:%M%p"

    def start_requests(self) -> Iterable[JsonRequest]:
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                yield JsonRequest(url=f"https://{domain}/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1")
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield JsonRequest(url=url)

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json():
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            item["name"] = item["name"].strip()
            item["street_address"] = item.pop("street")
            item["opening_hours"] = self.extract_opening_hours(item, feature)
            yield from self.post_process_item(item, response, feature) or []

    def extract_opening_hours(self, item: Feature, feature: dict) -> OpeningHours:
        oh = OpeningHours()
        if not feature.get("open_hours"):
            return oh
        hours_json = json.loads(feature["open_hours"])
        if hours_json == []:
            return oh

        for day_name, hours_ranges in hours_json.items():
            for hours_range in hours_ranges:
                hours_range = hours_range.upper()
                if not hours_range or hours_range == "0":
                    continue
                if hours_range == "1":
                    start_time = "12:00 AM"
                    end_time = "11:59 PM"
                else:
                    start_time = hours_range.split(" - ", 1)[0]
                    end_time = hours_range.split(" - ", 1)[1]
                if "AM" in start_time or "PM" in start_time or "AM" in end_time or "PM" in end_time:
                    oh.add_range(
                        DAYS_EN[day_name.title()],
                        start_time.replace(" AM", "AM").replace(" PM", "PM").replace(".", ":"),
                        end_time.replace(" AM", "AM").replace(" PM", "PM").replace(".", ":"),
                        self.time_format,
                    )
                else:
                    oh.add_range(DAYS_EN[day_name.title()], start_time, end_time)

        return oh

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
